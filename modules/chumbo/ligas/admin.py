from django.contrib import admin

from .models import Liga


@admin.register(Liga)
class LigaAdmin(admin.ModelAdmin):
    list_display = ("nome", "chave_cor", "sort_order", "is_active")
    list_filter = ("chave_cor", "is_active")
    search_fields = ("nome",)
    ordering = ("sort_order", "id")
