from django import forms

from .models import ModeloProduto


class ModeloForm(forms.ModelForm):
    class Meta:
        model = ModeloProduto
        fields = ["nome", "polaridade", "placas_por_grade", "tipo", "sort_order", "is_active"]
