from django.contrib import admin

from .models import Destino


@admin.register(Destino)
class DestinoAdmin(admin.ModelAdmin):
    list_display = ("nome", "slug", "sort_order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("nome", "slug")
    ordering = ("sort_order", "id")
