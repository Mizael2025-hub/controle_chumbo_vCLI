from django.db import models
from django.utils.text import slugify

from base.managers import ActiveManager
from base.models import BaseModel


class SharedMaster(BaseModel):
    """Base para cadastros cross-módulo (soft delete + ordenação)."""

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


class Setor(SharedMaster):
    nome = models.CharField(max_length=100, verbose_name="Nome")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="Slug")
    tipo = models.CharField(
        max_length=20,
        choices=[("producao", "Produção"), ("saida_direta", "Saída direta")],
        default="producao",
        verbose_name="Tipo",
    )

    class Meta(SharedMaster.Meta):
        verbose_name = "Setor"
        verbose_name_plural = "Setores"

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)


class Operador(SharedMaster):
    nome = models.CharField(max_length=100, verbose_name="Nome")

    class Meta(SharedMaster.Meta):
        verbose_name = "Operador"
        verbose_name_plural = "Operadores"

    def __str__(self):
        return self.nome


class Turno(SharedMaster):
    nome = models.CharField(max_length=100, verbose_name="Nome")

    class Meta(SharedMaster.Meta):
        verbose_name = "Turno"
        verbose_name_plural = "Turnos"

    def __str__(self):
        return self.nome


class Maquina(SharedMaster):
    nome = models.CharField(max_length=100, verbose_name="Nome")
    setor = models.ForeignKey(
        Setor,
        on_delete=models.PROTECT,
        related_name="maquinas",
        verbose_name="Setor",
    )

    class Meta(SharedMaster.Meta):
        verbose_name = "Máquina"
        verbose_name_plural = "Máquinas"

    def __str__(self):
        return f"{self.nome} · {self.setor}"
