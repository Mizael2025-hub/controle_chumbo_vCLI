from django.contrib import admin

from .models import Batch


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = (
        "liga",
        "numero_lote",
        "data_chegada",
        "peso_inicial_kg",
        "barras_iniciais",
        "colunas_grade",
        "linhas_grade",
    )
    list_filter = ("liga",)
    search_fields = ("numero_lote", "liga__nome")