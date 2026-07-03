from django.db import models


class ActiveManager(models.Manager):
    """Manager que filtra apenas registros ativos (soft delete)."""

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)
