from django import forms

from .models import Destino


class DestinoForm(forms.ModelForm):
    class Meta:
        model = Destino
        fields = ["nome", "slug", "sort_order", "is_active"]
