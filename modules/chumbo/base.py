from django.db import models

from base.managers import ActiveManager
from base.models import BaseModel


class ChumboMaster(BaseModel):
    """Base para cadastros específicos do módulo Chumbo (soft delete + ordem)."""

    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Ordem")
    created_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Criado por",
    )

    objects = models.Manager()
    active = ActiveManager()

    class Meta:
        abstract = True
        ordering = ("sort_order", "id")
