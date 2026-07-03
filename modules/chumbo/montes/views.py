from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View

from base.mixins import ModulePermMixin
from modules.chumbo.montes.models import Pile, PileEvent
from modules.chumbo.montes.services import (
    cancelar_reserva,
    devolver_almoxarifado,
    mover_para_setor,
    reservar,
    split,
)
from shared.models import Setor

from modules.chumbo.saida.forms import MoverForm, ReservaForm, SplitForm


class ReservaView(ModulePermMixin, View):
    """Criar reserva em monte (RF40-RF44)."""
    template_name = "chumbo/reserva.html"
    module_slug = "chumbo"
    required_module_role = "admin"

    def get(self, request, pk):
        pile = get_object_or_404(Pile, pk=pk, is_active=True)
        form = ReservaForm()
        return render(request, self.template_name, {"pile": pile, "form": form})

    def post(self, request, pk):
        pile = get_object_or_404(Pile, pk=pk, is_active=True)
        form = ReservaForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"pile": pile, "form": form})
        try:
            reservar(
                user=request.user,
                monte=pile,
                reservado_para=form.cleaned_data["reservado_para"],
                setor=form.cleaned_data.get("setor"),
            )
            messages.success(request, f"Monte {pile} reservado.")
        except ValueError as e:
            messages.error(request, str(e))
        return redirect("chumbo:estoque_lote", pk=pile.lote_id)


class CancelarReservaView(ModulePermMixin, View):
    module_slug = "chumbo"
    required_module_role = "admin"

    def post(self, request, pk):
        pile = get_object_or_404(Pile, pk=pk, is_active=True)
        try:
            cancelar_reserva(user=request.user, monte=pile)
            messages.success(request, "Reserva cancelada.")
        except ValueError as e:
            messages.error(request, str(e))
        return redirect("chumbo:estoque_lote", pk=pile.lote_id)


class MoverView(ModulePermMixin, View):
    """Mover monte ao setor (RF50)."""
    template_name = "chumbo/mover.html"
    module_slug = "chumbo"
    required_module_role = "admin"

    def get(self, request, pk):
        pile = get_object_or_404(Pile, pk=pk, is_active=True)
        return render(request, self.template_name, {"pile": pile, "form": MoverForm()})

    def post(self, request, pk):
        pile = get_object_or_404(Pile, pk=pk, is_active=True)
        form = MoverForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"pile": pile, "form": form})
        try:
            mover_para_setor(user=request.user, monte=pile, setor=form.cleaned_data["setor"])
            messages.success(request, f"Monte {pile} movido ao setor.")
        except ValueError as e:
            messages.error(request, str(e))
        return redirect("chumbo:estoque_lote", pk=pile.lote_id)


class DevolverView(ModulePermMixin, View):
    """Devolver monte ao almoxarifado (RF51). ARC-04: preserva reserva por padrão."""
    module_slug = "chumbo"
    required_module_role = "admin"

    def post(self, request, pk):
        pile = get_object_or_404(Pile, pk=pk, is_active=True)
        preservar = request.POST.get("preservar_reserva", "1") != "0"
        try:
            devolver_almoxarifado(user=request.user, monte=pile, preservar_reserva=preservar)
            messages.success(request, f"Monte {pile} devolvido ao almoxarifado.")
        except ValueError as e:
            messages.error(request, str(e))
        return redirect("chumbo:estoque_lote", pk=pile.lote_id)


class SplitView(ModulePermMixin, View):
    """Movimentação parcial — split (RF52)."""
    template_name = "chumbo/split.html"
    module_slug = "chumbo"
    required_module_role = "admin"

    def get(self, request, pk):
        pile = get_object_or_404(Pile, pk=pk, is_active=True)
        return render(request, self.template_name, {"pile": pile, "form": SplitForm()})

    def post(self, request, pk):
        pile = get_object_or_404(Pile, pk=pk, is_active=True)
        form = SplitForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"pile": pile, "form": form})
        try:
            filho = split(
                user=request.user,
                monte=pile,
                barras=form.cleaned_data["barras"],
                peso_kg=form.cleaned_data["peso_kg"],
            )
            messages.success(request, f"Split criado: novo monte {filho.posicao_x},{filho.posicao_y}.")
        except ValueError as e:
            messages.error(request, str(e))
        return redirect("chumbo:estoque_lote", pk=pile.lote_id)


class EventosView(ModulePermMixin, View):
    """Histórico de eventos por monte (RF17)."""
    template_name = "chumbo/eventos.html"
    module_slug = "chumbo"
    required_module_role = ("operador", "admin")

    def get(self, request, pk):
        pile = get_object_or_404(Pile, pk=pk, is_active=True)
        eventos = PileEvent.objects.filter(monte=pile).select_related("created_by")
        return render(request, self.template_name, {"pile": pile, "eventos": eventos})