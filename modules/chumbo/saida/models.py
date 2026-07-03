import uuid

from django.db import models

from base.models import BaseModel
from modules.chumbo.destinos.models import Destino
from modules.chumbo.montes.models import Pile


class TransacaoSaida(BaseModel):
    monte = models.ForeignKey(
        Pile,
        on_delete=models.PROTECT,
        related_name="saidas",
        verbose_name="Monte",
    )
    peso_baixado_kg = models.DecimalField(
        max_digits=12, decimal_places=3, verbose_name="Peso baixado (kg)"
    )
    barras_baixadas = models.PositiveIntegerField(verbose_name="Barras baixadas")
    destino = models.ForeignKey(
        Destino,
        on_delete=models.PROTECT,
        related_name="transacoes",
        verbose_name="Destino",
    )
    setor = models.ForeignKey(
        "shared.Setor",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name="Setor",
    )
    data_transacao = models.DateTimeField(verbose_name="Data da transação")
    grupo_liberacao = models.UUIDField(
        default=uuid.uuid4, verbose_name="Grupo de liberação"
    )
    observacao = models.TextField(blank=True, default="", verbose_name="Observação")
    estornada = models.BooleanField(default=False, verbose_name="Estornada")
    estornada_em = models.DateTimeField(null=True, blank=True, verbose_name="Estornada em")
    estornada_por = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Estornada por",
    )
    created_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Criado por",
    )

    class Meta:
        verbose_name = "Transação de saída"
        verbose_name_plural = "Transações de saída"
        ordering = ("-data_transacao", "-id")

    def __str__(self):
        return f"{self.monte} → {self.destino} · {self.peso_baixado_kg}kg"