from django.db import models
from django.utils.text import slugify

from modules.chumbo.base import ChumboMaster


class Destino(ChumboMaster):
    nome = models.CharField(max_length=100, verbose_name="Nome")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="Slug")

    class Meta(ChumboMaster.Meta):
        verbose_name = "Destino de saída"
        verbose_name_plural = "Destinos de saída"

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)
