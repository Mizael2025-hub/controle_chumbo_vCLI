from decimal import Decimal

from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View

from base.mixins import ModulePermMixin
from modules.chumbo.destinos.models import Destino
from modules.chumbo.montes.models import Pile
from modules.chumbo.montes.services import baixar_grupo, estornar
from shared.models import Setor

from .forms import LiberacaoForm
from .models import TransacaoSaida


class LiberacaoView(ModulePermMixin, View):
    """Liberação agrupada (RF30-RF36). Seleciona montes na grade e baixa em
    lote. UI de parcial recalcula kg quando barras mudam (ARC-03)."""
    template_name = "chumbo/liberacao.html"
    module_slug = "chumbo"
    required_module_role = "admin"

    def get(self, request):
        lote_id = request.GET.get("lote")
        montes = Pile.objects.filter(is_active=True, lote__is_active=True).select_related("lote", "lote__liga")
        if lote_id:
            montes = montes.filter(lote_id=lote_id)
        montes = montes.exclude(status="CONSUMIDO").order_by("lote", "posicao_y", "posicao_x")
        form = LiberacaoForm(montes_ids=[m.id for m in montes])
        return render(request, self.template_name, {
            "form": form, "montes": montes, "destinos": Destino.objects.filter(is_active=True),
        })

    def post(self, request):
        montes = Pile.objects.filter(is_active=True, lote__is_active=True).exclude(status="CONSUMIDO")
        montes = list(montes.select_related("lote", "lote__liga").order_by("lote", "posicao_y", "posicao_x"))
        form = LiberacaoForm(request.POST, montes_ids=[m.id for m in montes])
        if not form.is_valid():
            return render(request, self.template_name, {
                "form": form, "montes": montes, "destinos": Destino.objects.filter(is_active=True),
            })

        itens = []
        for m in montes:
            barras = request.POST.get(f"monte_{m.id}_barras")
            peso = request.POST.get(f"monte_{m.id}_peso")
            if not barras or not peso:
                continue
            try:
                b = int(barras)
                p = Decimal(str(peso).replace(",", "."))
            except (ValueError, TypeError):
                continue
            if b <= 0 or p <= 0:
                continue
            if b > m.barras_atuais or p > m.peso_atual_kg:
                form.add_error(None, f"Monte {m} ({m.posicao_x},{m.posicao_y}): saldo insuficiente.")
                continue
            itens.append({"monte": m, "barras": b, "peso_kg": p})

        if form.errors or not itens:
            if not itens and not form.errors:
                form.add_error(None, "Selecione ao menos um monte com barras e peso.")
            return render(request, self.template_name, {
                "form": form, "montes": montes, "destinos": Destino.objects.filter(is_active=True),
            })

        try:
            grupo, trxs = baixar_grupo(
                user=request.user,
                itens=itens,
                destino=form.cleaned_data["destino"],
                setor=form.cleaned_data.get("setor"),
                observacao=form.cleaned_data.get("observacao", ""),
            )
        except ValueError as e:
            form.add_error(None, str(e))
            return render(request, self.template_name, {
                "form": form, "montes": montes, "destinos": Destino.objects.filter(is_active=True),
            })

        messages.success(request, f"Liberação {str(grupo)[:8]} criada com {len(trxs)} monte(s).")
        return redirect("chumbo:liberacao_hist")


class LiberacaoHistoricoView(ModulePermMixin, View):
    template_name = "chumbo/liberacao_hist.html"
    module_slug = "chumbo"
    required_module_role = ("operador", "admin")

    def get(self, request):
        trxs = (
            TransacaoSaida.objects.select_related("monte", "monte__lote", "monte__lote__liga", "destino", "created_by")
            .order_by("-data_transacao", "-id")
        )
        return render(request, self.template_name, {"trxs": trxs})


class EstornoView(ModulePermMixin, View):
    module_slug = "chumbo"
    required_module_role = "admin"

    def post(self, request, pk):
        trx = get_object_or_404(TransacaoSaida, pk=pk)
        try:
            estornar(user=request.user, transacao=trx, observacao=request.POST.get("observacao", ""))
            messages.success(request, "Liberação estornada.")
        except ValueError as e:
            messages.error(request, str(e))
        return redirect("chumbo:liberacao_hist")