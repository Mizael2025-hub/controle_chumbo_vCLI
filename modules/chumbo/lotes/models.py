from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from base.managers import ActiveManager
from base.models import BaseModel
from modules.chumbo.ligas.models import Liga


class Batch(BaseModel):
    liga = models.ForeignKey(
        Liga,
        on_delete=models.PROTECT,
        related_name="lotes",
        verbose_name="Liga",
    )
    numero_lote = models.CharField(max_length=50, verbose_name="Número do lote")
    data_chegada = models.DateField(verbose_name="Data de chegada")
    peso_inicial_kg = models.DecimalField(
        max_digits=12, decimal_places=3, verbose_name="Peso inicial (kg)"
    )
    barras_iniciais = models.PositiveIntegerField(verbose_name="Barras iniciais")
    colunas_grade = models.PositiveIntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name="Colunas da grade",
    )
    linhas_grade = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Linhas da grade",
    )
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
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
        verbose_name = "Lote"
        verbose_name_plural = "Lotes"
        ordering = ("-data_chegada", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=["liga", "numero_lote"], name="unique_liga_numero_lote"
            )
        ]

    def __str__(self):
        return f"{self.liga} · {self.numero_lote}"