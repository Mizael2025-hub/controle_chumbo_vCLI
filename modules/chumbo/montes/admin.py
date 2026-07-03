from django.contrib import admin

from .models import Pile, PileEvent


@admin.register(Pile)
class PileAdmin(admin.ModelAdmin):
    list_display = ("lote", "posicao_x", "posicao_y", "peso_atual_kg", "barras_atuais", "status", "localizacao")
    list_filter = ("status", "localizacao", "lote__liga")
    search_fields = ("lote__numero_lote", "lote__liga__nome")


@admin.register(PileEvent)
class PileEventAdmin(admin.ModelAdmin):
    list_display = ("monte", "tipo", "created_at", "created_by")
    list_filter = ("tipo",)