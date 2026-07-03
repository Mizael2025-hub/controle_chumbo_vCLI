from django import forms

from .models import Maquina, Operador, Setor, Turno


class SetorForm(forms.ModelForm):
    class Meta:
        model = Setor
        fields = ["nome", "slug", "tipo", "sort_order", "is_active"]


class OperadorForm(forms.ModelForm):
    class Meta:
        model = Operador
        fields = ["nome", "sort_order", "is_active"]


class TurnoForm(forms.ModelForm):
    class Meta:
        model = Turno
        fields = ["nome", "sort_order", "is_active"]


class MaquinaForm(forms.ModelForm):
    class Meta:
        model = Maquina
        fields = ["nome", "setor", "sort_order", "is_active"]
