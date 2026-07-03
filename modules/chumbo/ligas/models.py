from django.db import models

from modules.chumbo.base import ChumboMaster


class CorChave(models.TextChoices):
    AZUL = "azul", "Azul"
    AMARELO = "amarelo", "Amarelo"
    VERMELHO = "vermelho", "Vermelho"
    PRETO = "preto", "Preto"
    CINZA = "cinza", "Cinza"
    SEM_COR = "sem_cor", "Sem cor"
    VERDE = "verde", "Verde"
    BRANCO = "branco", "Branco"


class Liga(ChumboMaster):
    nome = models.CharField(max_length=100, verbose_name="Nome")
    chave_cor = models.CharField(
        max_length=20,
        choices=CorChave.choices,
        default=CorChave.SEM_COR,
        verbose_name="Cor",
    )

    class Meta(ChumboMaster.Meta):
        verbose_name = "Liga"
        verbose_name_plural = "Ligas"

    def __str__(self):
        return self.nome
