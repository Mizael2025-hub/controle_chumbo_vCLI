from django.db import models

from base.models import BaseModel


class ModulePermission(BaseModel):
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="module_perms",
        verbose_name="Usuário",
    )
    module_slug = models.CharField(max_length=50, verbose_name="Módulo")
    role = models.CharField(
        max_length=20,
        choices=[("admin", "Administrador"), ("operador", "Operador")],
        verbose_name="Função no módulo",
    )

    class Meta:
        unique_together = ("user", "module_slug")
        ordering = ("-created_at",)
        verbose_name = "Permissão de módulo"
        verbose_name_plural = "Permissões de módulo"

    def __str__(self):
        return f"{self.user} · {self.module_slug} · {self.role}"
