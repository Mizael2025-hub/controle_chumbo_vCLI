from django.contrib import admin

from .models import Maquina, Operador, Setor, Turno


@admin.register(Setor)
class SetorAdmin(admin.ModelAdmin):
    list_display = ("nome", "slug", "tipo", "sort_order", "is_active")
    list_filter = ("tipo", "is_active")
    search_fields = ("nome", "slug")
    ordering = ("sort_order", "id")


@admin.register(Operador)
class OperadorAdmin(admin.ModelAdmin):
    list_display = ("nome", "sort_order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("nome",)
    ordering = ("sort_order", "id")


@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = ("nome", "sort_order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("nome",)
    ordering = ("sort_order", "id")


@admin.register(Maquina)
class MaquinaAdmin(admin.ModelAdmin):
    list_display = ("nome", "setor", "sort_order", "is_active")
    list_filter = ("is_active", "setor")
    search_fields = ("nome",)
    ordering = ("sort_order", "id")
