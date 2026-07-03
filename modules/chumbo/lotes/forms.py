from datetime import date

from django import forms

from .models import Batch


class BatchStep1Form(forms.ModelForm):
    data_chegada = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        input_formats=["%Y-%m-%d", "%d/%m/%Y"],
        label="Data de chegada",
    )

    class Meta:
        model = Batch
        fields = [
            "liga",
            "numero_lote",
            "data_chegada",
            "colunas_grade",
            "linhas_grade",
        ]
        labels = {
            "numero_lote": "Número do lote",
            "colunas_grade": "Colunas da grade (1-10)",
            "linhas_grade": "Linhas da grade (1-5)",
        }

    def clean_data_chegada(self):
        valor = self.cleaned_data["data_chegada"]
        if valor and valor > date.today():
            raise forms.ValidationError("A data de chegada não pode ser futura.")
        return valor

    def clean(self):
        cleaned = super().clean()
        liga = cleaned.get("liga")
        numero = cleaned.get("numero_lote")
        if liga and numero:
            qs = Batch.objects.filter(liga=liga, numero_lote=numero)
            if qs.exists():
                raise forms.ValidationError(
                    "Já existe um lote com este número para esta liga."
                )
        return cleaned


def make_grade_form(cols: int, rows: int):
    """Gera uma classe de Form dinâmica com campos peso_<x>_<y> e
    barras_<x>_<y> para cada célula da grade."""
    declarative = {}
    for y in range(rows):
        for x in range(cols):
            declarative[f"peso_{x}_{y}"] = forms.DecimalField(
                required=False,
                max_digits=12,
                decimal_places=3,
                min_value=0,
                widget=forms.NumberInput(attrs={"inputmode": "decimal", "placeholder": "kg"}),
                label=f"Peso (kg) x{x} y{y}",
            )
            declarative[f"barras_{x}_{y}"] = forms.IntegerField(
                required=False,
                min_value=0,
                widget=forms.NumberInput(attrs={"inputmode": "numeric", "placeholder": "bar"}),
                label=f"Barras x{x} y{y}",
            )
    return type("GradeForm", (forms.Form,), declarative)