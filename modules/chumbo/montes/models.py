from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from base.managers import ActiveManager
from base.models import BaseModel


class PileStatus(models.TextChoices):
    DISPONIVEL = "DISPONIVEL", "Disponível"
    RESERVADO = "RESERVADO", "Reservado"
    PARCIAL = "PARCIAL", "Parcial"
    CONSUMIDO = "CONSUMIDO", "Consumido"


class Localizacao(models.TextChoices):
    ALMOXARIFADO = "almoxarifado", "Almoxarifado"
    SETOR = "setor", "Setor"


class EventType(models.TextChoices):
    RESERVA = "RESERVA", "Reserva"
    CANCELAMENTO_RESERVA = "CANCELAMENTO_RESERVA", "Cancelamento de reserva"
    BAIXA_PARCIAL = "BAIXA_PARCIAL", "Baixa parcial"
    BAIXA_TOTAL = "BAIXA_TOTAL", "Baixa total"
    MOVIDO_PARA_SETOR = "MOVIDO_PARA_SETOR", "Movido para setor"
    DEVOLVIDO_ALMOXARIFADO = "DEVOLVIDO_ALMOXARIFADO", "Devolvido ao almoxarifado"
    ESTORNO = "ESTORNO", "Estorno"
    SPLIT_CRIADO = "SPLIT_CRIADO", "Split criado"
    CONSUMO_ALOCADO = "CONSUMO_ALOCADO", "Consumo alocado"


class Pile(BaseModel):
    lote = models.ForeignKey(
        "chumbo_lotes.Batch",
        on_delete=models.CASCADE,
        related_name="montes",
        verbose_name="Lote",
    )
    peso_atual_kg = models.DecimalField(
        max_digits=12, decimal_places=3, default=0, verbose_name="Peso atual (kg)"
    )
    barras_atuais = models.PositiveIntegerField(
        default=0, verbose_name="Barras atuais"
    )
    posicao_x = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(99)],
        verbose_name="Posição X",
    )
    posicao_y = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        verbose_name="Posição Y",
    )
    status = models.CharField(
        max_length=20,
        choices=PileStatus.choices,
        default=PileStatus.DISPONIVEL,
        verbose_name="Status",
    )
    reservado_para = models.CharField(
        max_length=100, blank=True, default="", verbose_name="Reservado para"
    )
    reservado_em = models.DateTimeField(null=True, blank=True, verbose_name="Reservado em")
    setor_reserva = models.ForeignKey(
        "shared.Setor",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name="Setor da reserva",
    )
    grupo_reserva_id = models.UUIDField(
        null=True, blank=True, verbose_name="Grupo de reserva"
    )
    localizacao = models.CharField(
        max_length=20,
        choices=Localizacao.choices,
        default=Localizacao.ALMOXARIFADO,
        verbose_name="Localização",
    )
    setor = models.ForeignKey(
        "shared.Setor",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="montes_no_setor",
        verbose_name="Setor",
    )
    movido_setor_em = models.DateTimeField(null=True, blank=True, verbose_name="Movido ao setor em")
    monte_origem = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="filhos",
        verbose_name="Monte de origem (split)",
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
        verbose_name = "Monte"
        verbose_name_plural = "Montes"
        ordering = ("posicao_y", "posicao_x")
        constraints = [
            models.UniqueConstraint(
                fields=["lote", "posicao_x", "posicao_y"], name="unique_lote_posicao"
            )
        ]

    def __str__(self):
        return f"{self.lote} · ({self.posicao_x},{self.posicao_y})"


class PileEvent(BaseModel):
    monte = models.ForeignKey(
        Pile,
        on_delete=models.CASCADE,
        related_name="eventos",
        verbose_name="Monte",
    )
    tipo = models.CharField(max_length=30, choices=EventType.choices, verbose_name="Tipo")
    dados = models.JSONField(null=True, blank=True, verbose_name="Dados")
    created_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Criado por",
    )

    class Meta:
        verbose_name = "Evento de monte"
        verbose_name_plural = "Eventos de monte"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.monte} · {self.get_tipo_display()}"