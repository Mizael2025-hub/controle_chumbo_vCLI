from decimal import Decimal

from django.db import transaction

from modules.chumbo.ligas.models import Liga
from modules.chumbo.montes.models import Pile

from .models import Batch


def criar_lote_com_grade(
    *,
    user,
    liga_id,
    numero_lote,
    data_chegada,
    peso_inicial_kg,
    barras_iniciais,
    colunas_grade,
    linhas_grade,
    celulas,
):
    """Cria o lote e seus montes atomicamente. ARC-02: trava a liga com
    select_for_update dentro da transação para evitar órfão se a liga for
    removida entre checagem e inserção."""
    with transaction.atomic():
        liga = Liga.objects.select_for_update().get(pk=liga_id)
        batch = Batch.objects.create(
            liga=liga,
            numero_lote=numero_lote,
            data_chegada=data_chegada,
            peso_inicial_kg=peso_inicial_kg,
            barras_iniciais=barras_iniciais,
            colunas_grade=colunas_grade,
            linhas_grade=linhas_grade,
            created_by=user,
        )
        piles = []
        for (x, y), (kg, barras) in celulas.items():
            if kg or barras:
                piles.append(
                    Pile(
                        lote=batch,
                        posicao_x=x,
                        posicao_y=y,
                        peso_atual_kg=kg or Decimal("0"),
                        barras_atuais=barras or 0,
                        created_by=user,
                    )
                )
        if piles:
            Pile.objects.bulk_create(piles)
        return batch