from django.contrib.auth.models import AbstractUser
from django.db import models

from base.models import BaseModel


class Role(models.TextChoices):
    ADMIN = "admin", "Administrador"
    OPERATOR = "operador", "Operador"


class User(AbstractUser, BaseModel):
    username = None
    email = models.EmailField(unique=True, verbose_name="E-mail")
    name = models.CharField(max_length=255, verbose_name="Nome")
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.OPERATOR,
        verbose_name="Função",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    class Meta(AbstractUser.Meta):
        ordering = ("-created_at",)
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self):
        return self.email

    @property
    def is_admin(self):
        return self.is_superuser or self.role == Role.ADMIN

    def has_module_role(self, slug, role):
        if self.is_admin:
            return True
        return self.module_perms.filter(module_slug=slug, role=role).exists()


from .module_perms import ModulePermission  # noqa: E402,F401  (registra o model)
