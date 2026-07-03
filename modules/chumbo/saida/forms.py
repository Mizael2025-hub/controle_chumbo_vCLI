from decimal import Decimal

from django import forms

from modules.chumbo.destinos.models import Destino
from modules.chumbo.montes.models import Pile
from shared.models import Setor


class LiberacaoForm(forms.Form):
    destino = forms.ModelChoiceField(
        Destino.objects.filter(is_active=True), label="Destino"
    )
    setor = forms.ModelChoiceField(
        Setor.objects.filter(is_active=True), required=False, label="Setor (opcional)"
    )
    observacao = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"rows": 2}), label="Observação"
    )

    def __init__(self, *args, montes_ids=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.montes_ids = montes_ids or []

    def clean(self):
        cleaned = super().clean()
        erros = []
        for mid in self.montes_ids:
            prefix = f"monte_{mid}_"
            barras = self.data.get(prefix + "barras")
            peso = self.data.get(prefix + "peso")
            if not any([barras, peso]):
                continue
            if not barras or not peso:
                erros.append(f"Monte {mid}: preencha barras e peso juntos.")
                continue
            try:
                b = int(barras)
                p = Decimal(str(peso).replace(",", "."))
                if b <= 0 or p <= 0:
                    erros.append(f"Monte {mid}: valores devem ser > 0.")
            except (ValueError, TypeError):
                erros.append(f"Monte {mid}: valores inválidos.")
        if erros:
            raise forms.ValidationError(erros)
        return cleaned


class ReservaForm(forms.Form):
    reservado_para = forms.CharField(max_length=100, label="Reservado para")
    setor = forms.ModelChoiceField(
        Setor.objects.filter(is_active=True), required=False, label="Setor"
    )


class MoverForm(forms.Form):
    setor = forms.ModelChoiceField(
        Setor.objects.filter(is_active=True), label="Setor de destino"
    )


class SplitForm(forms.Form):
    barras = forms.IntegerField(min_value=1, label="Barras do novo monte")
    peso_kg = forms.DecimalField(
        max_digits=12, decimal_places=3, min_value=Decimal("0.001"), label="Peso do novo monte (kg)"
    )