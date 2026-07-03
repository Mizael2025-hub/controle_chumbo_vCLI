from django.contrib import admin

from .models import TransacaoSaida


@admin.register(TransacaoSaida)
class TransacaoSaidaAdmin(admin.ModelAdmin):
    list_display = (
        "monte",
        "destino",
        "peso_baixado_kg",
        "barras_baixadas",
        "data_transacao",
        "estornada",
        "created_by",
    )
    list_filter = ("destino", "estornada")
    search_fields = ("monte__lote__numero_lote",)