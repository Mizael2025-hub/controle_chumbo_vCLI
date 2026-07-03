from django import forms

from .models import Liga


class LigaForm(forms.ModelForm):
    class Meta:
        model = Liga
        fields = ["nome", "chave_cor", "sort_order", "is_active"]
