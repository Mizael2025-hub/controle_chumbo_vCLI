import datetime
from decimal import Decimal

from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, ListView, View

from base.mixins import ModulePermMixin
from shared.models import Setor

from .forms import BatchStep1Form, make_grade_form
from .models import Batch
from .services import criar_lote_com_grade


class LoteStep1View(ModulePermMixin, View):
    """Etapa 1 do recebimento: dados do lote + dimensões da grade."""
    template_name = "chumbo/lote_step1.html"
    module_slug = "chumbo"
    required_module_role = "admin"

    def get(self, request):
        return render(request, self.template_name, {"form": BatchStep1Form()})

    def post(self, request):
        form = BatchStep1Form(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})
        cd = form.cleaned_data
        request.session["lote_step1"] = {
            "liga_id": cd["liga"].id,
            "liga_nome": cd["liga"].nome,
            "numero_lote": cd["numero_lote"],
            "data_chegada": cd["data_chegada"].isoformat(),
            "colunas_grade": cd["colunas_grade"],
            "linhas_grade": cd["linhas_grade"],
        }
        return redirect("chumbo:lote_step2")


class LoteStep2View(ModulePermMixin, View):
    """Etapa 2: distribuir kg/barras pelas células da grade."""
    template_name = "chumbo/lote_step2.html"
    module_slug = "chumbo"
    required_module_role = "admin"

    def _step1(self, request):
        return request.session.get("lote_step1")

    def _cells(self, form, cols, rows):
        grid = []
        for y in range(rows):
            row = []
            for x in range(cols):
                row.append({
                    "x": x,
                    "y": y,
                    "peso": form[f"peso_{x}_{y}"],
                    "barras": form[f"barras_{x}_{y}"],
                })
            grid.append(row)
        return grid

    def get(self, request):
        s1 = self._step1(request)
        if not s1:
            return redirect("chumbo:lote_step1")
        cols = s1["colunas_grade"]
        rows = s1["linhas_grade"]
        form = make_grade_form(cols, rows)()
        return render(
            request,
            self.template_name,
            {"form": form, "cols": cols, "rows": rows, "s1": s1, "cells": self._cells(form, cols, rows)},
        )

    def post(self, request):
        s1 = self._step1(request)
        if not s1:
            return redirect("chumbo:lote_step1")
        cols = s1["colunas_grade"]
        rows = s1["linhas_grade"]
        form = make_grade_form(cols, rows)(request.POST)
        if not form.is_valid():
            return render(
                request, self.template_name, {"form": form, "cols": cols, "rows": rows, "s1": s1, "cells": self._cells(form, cols, rows)}
            )

        celulas = {}
        for y in range(rows):
            for x in range(cols):
                kg = form.cleaned_data.get(f"peso_{x}_{y}") or Decimal("0")
                barras = form.cleaned_data.get(f"barras_{x}_{y}") or 0
                if (kg and kg > 0) or barras:
                    celulas[(x, y)] = (kg, barras)

        soma_kg = sum((c[0] for c in celulas.values()), Decimal("0"))
        soma_barras = sum(c[1] for c in celulas.values())

        if not celulas or soma_kg <= 0 or soma_barras <= 0:
            form.add_error(None, "Preencha ao menos uma célula da grade com kg e barras maiores que zero.")
        if form.errors:
            return render(
                request, self.template_name, {"form": form, "cols": cols, "rows": rows, "s1": s1, "cells": self._cells(form, cols, rows)}
            )

        batch = criar_lote_com_grade(
            user=request.user,
            liga_id=s1["liga_id"],
            numero_lote=s1["numero_lote"],
            data_chegada=datetime.date.fromisoformat(s1["data_chegada"]),
            peso_inicial_kg=soma_kg,
            barras_iniciais=soma_barras,
            colunas_grade=cols,
            linhas_grade=rows,
            celulas=celulas,
        )
        request.session.pop("lote_step1", None)
        messages.success(request, f"Lote {batch} criado com {len(celulas)} monte(s).")
        return redirect("chumbo:estoque_lote", pk=batch.pk)


class EstoqueListView(ModulePermMixin, ListView):
    """Estoque: lista lotes ativos com saldo (soma dos montes)."""
    template_name = "chumbo/estoque_list.html"
    context_object_name = "lotes"
    module_slug = "chumbo"
    required_module_role = ("operador", "admin")

    def get_queryset(self):
        return Batch.objects.filter(is_active=True).select_related("liga").order_by("-data_chegada", "-id")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        saldos = []
        for b in ctx["lotes"]:
            agg = b.montes.filter(is_active=True).aggregate(
                k=Sum("peso_atual_kg"), barras=Sum("barras_atuais")
            )
            saldos.append((b, agg["k"] or Decimal("0"), agg["barras"] or 0))
        ctx["saldos"] = saldos
        return ctx


class EstoqueGradeView(ModulePermMixin, DetailView):
    """Grade 2D do lote com métricas de balanço (ARC-14: min-cell 40px)."""
    template_name = "chumbo/estoque_grade.html"
    context_object_name = "lote"
    module_slug = "chumbo"
    required_module_role = ("operador", "admin")

    def get_queryset(self):
        return Batch.objects.filter(is_active=True).select_related("liga")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        lote = self.object
        piles = list(
            lote.montes.filter(is_active=True).order_by("posicao_y", "posicao_x")
        )
        grid = {(p.posicao_x, p.posicao_y): p for p in piles}
        piles_json = [
            {
                "pk": p.pk,
                "pos": f"x{p.posicao_x} · y{p.posicao_y}",
                "kg": f"{p.peso_atual_kg:.3f}",
                "barras": p.barras_atuais,
                "status": p.get_status_display(),
                "local": p.get_localizacao_display(),
                "urlReserva": reverse("chumbo:reservar_create", args=[p.pk]),
                "urlMover": reverse("chumbo:mover", args=[p.pk]),
                "urlSplit": reverse("chumbo:split", args=[p.pk]),
                "urlEventos": reverse("chumbo:eventos", args=[p.pk]),
                "urlDevolver": reverse("chumbo:devolver", args=[p.pk]),
            }
            for p in piles
        ]
        matrix = []
        for y in range(lote.linhas_grade):
            row = []
            for x in range(lote.colunas_grade):
                p = grid.get((x, y))
                row.append({
                    "pile": p,
                    "x": x,
                    "y": y,
                    "ocupado": p is not None,
                })
            matrix.append(row)

        estoque_kg = sum((p.peso_atual_kg for p in piles), Decimal("0"))
        estoque_barras = sum(p.barras_atuais for p in piles)
        reservado_kg = sum(
            (p.peso_atual_kg for p in piles if p.status == "RESERVADO"),
            Decimal("0"),
        )
        reservado_barras = sum(
            p.barras_atuais for p in piles if p.status == "RESERVADO"
        )

        ctx.update({
            "piles": piles,
            "piles_json": piles_json,
            "setores_json": [
                {"id": s.id, "nome": s.nome}
                for s in Setor.objects.filter(is_active=True).order_by("sort_order", "id")
            ],
            "grid": grid,
            "matrix": matrix,
            "cols": lote.colunas_grade,
            "rows": lote.linhas_grade,
            "estoque_kg": estoque_kg,
            "estoque_barras": estoque_barras,
            "reservado_kg": reservado_kg,
            "reservado_barras": reservado_barras,
            "disponivel_kg": estoque_kg - reservado_kg,
            "disponivel_barras": estoque_barras - reservado_barras,
            "liga_cor": lote.liga.chave_cor,
        })
        return ctx