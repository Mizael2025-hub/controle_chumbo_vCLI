from django.contrib import admin

from .models import ModeloProduto


@admin.register(ModeloProduto)
class ModeloProdutoAdmin(admin.ModelAdmin):
    list_display = ("nome", "polaridade", "placas_por_grade", "tipo", "is_active")
    list_filter = ("polaridade", "tipo", "is_active")
    search_fields = ("nome",)
    ordering = ("sort_order", "id")
