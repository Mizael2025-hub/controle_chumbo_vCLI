from django.db import models

from modules.chumbo.base import ChumboMaster


class Polaridade(models.TextChoices):
    POSITIVA = "positiva", "Positiva"
    NEGATIVA = "negativa", "Negativa"


class ModeloProduto(ChumboMaster):
    nome = models.CharField(max_length=100, verbose_name="Nome")
    polaridade = models.CharField(
        max_length=10,
        choices=Polaridade.choices,
        default=Polaridade.POSITIVA,
        verbose_name="Polaridade",
    )
    placas_por_grade = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Placas por grade"
    )
    tipo = models.CharField(max_length=20, default="grade", verbose_name="Tipo")

    class Meta(ChumboMaster.Meta):
        verbose_name = "Modelo de produto"
        verbose_name_plural = "Modelos de produto"

    def __str__(self):
        return self.nome
