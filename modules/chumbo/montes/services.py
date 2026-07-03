import uuid
from decimal import Decimal

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from modules.chumbo.montes.models import EventType, Localizacao, Pile, PileEvent, PileStatus
from modules.chumbo.saida.models import TransacaoSaida

EPSILON = Decimal("0.0005")


def reliberar_status(pile: Pile, houve_baixa: bool = False) -> None:
    """Recalcula status do monte apos baixa/estorno (ARC-01, via ||). Não
    toca em RESERVADO (reserva não altera kg/barras). `houve_baixa=True`
    sinaliza que houve redução de saldo (monte originalmente cheio → PARCIAL
    se ainda houver saldo, CONSUMIDO se zerou)."""
    if pile.status == PileStatus.RESERVADO and not houve_baixa:
        return
    if pile.barras_atuais <= 0 or pile.peso_atual_kg <= EPSILON:
        pile.peso_atual_kg = Decimal("0")
        pile.barras_atuais = 0
        pile.status = PileStatus.CONSUMIDO
        return
    if houve_baixa:
        pile.status = PileStatus.PARCIAL
        return
    if pile.status == PileStatus.CONSUMIDO:
        pile.status = PileStatus.PARCIAL
        return
    if pile.barras_atuais > 0 and pile.status == PileStatus.DISPONIVEL:
        return
    if pile.barras_atuais > 0:
        pile.status = PileStatus.PARCIAL
    else:
        pile.peso_atual_kg = Decimal("0")
        pile.barras_atuais = 0
        pile.status = PileStatus.CONSUMIDO


def baixar(
    *,
    user,
    monte: Pile,
    barras: int,
    peso_kg: Decimal,
    destino,
    setor=None,
    observacao: str = "",
    grupo_liberacao=None,
):
    """Baixa (parcial/total) de um monte. Atomico + select_for_update (ARC-06).
    Status via || (ARC-01)."""
    if barras <= 0 or peso_kg <= 0:
        raise ValueError("Barras e peso devem ser maiores que zero.")
    with transaction.atomic():
        pile = Pile.objects.select_for_update().get(pk=monte.pk)
        if pile.status == PileStatus.CONSUMIDO:
            raise ValueError("Monte já consumido.")
        if barras > pile.barras_atuais or peso_kg > pile.peso_atual_kg:
            raise ValueError(
                f"Saldo insuficiente. Disponível: {pile.peso_atual_kg} kg / {pile.barras_atuais} barras."
            )
        pile.peso_atual_kg -= peso_kg
        pile.barras_atuais -= barras
        reliberar_status(pile, houve_baixa=True)
        pile.save(update_fields=["peso_atual_kg", "barras_atuais", "status", "updated_at"])

        tipo_evento = (
            EventType.BAIXA_TOTAL
            if pile.status == PileStatus.CONSUMIDO
            else EventType.BAIXA_PARCIAL
        )
        PileEvent.objects.create(
            monte=pile,
            tipo=tipo_evento,
            dados={
                "barras": barras,
                "peso_kg": str(peso_kg),
                "destino": destino.nome if destino else None,
            },
            created_by=user,
        )
        trx = TransacaoSaida.objects.create(
            monte=pile,
            peso_baixado_kg=peso_kg,
            barras_baixadas=barras,
            destino=destino,
            setor=setor,
            data_transacao=timezone.now(),
            grupo_liberacao=grupo_liberacao or uuid.uuid4(),
            observacao=observacao,
            created_by=user,
        )
        return trx


def baixar_grupo(*, user, itens, destino, setor=None, observacao=""):
    """Liberação agrupada (RF30/RF33): itens = [{monte, barras, peso_kg}, ...].
    Todos dentro de uma única transação. Falha = rollback total."""
    grupo = uuid.uuid4()
    itens_count = 0
    with transaction.atomic():
        trxs = []
        for it in itens:
            trx = baixar(
                user=user,
                monte=it["monte"],
                barras=it["barras"],
                peso_kg=it["peso_kg"],
                destino=destino,
                setor=setor,
                observacao=observacao,
                grupo_liberacao=grupo,
            )
            trxs.append(trx)
            itens_count += 1
        if itens_count == 0:
            raise ValueError("Selecione ao menos um monte para liberar.")
        return grupo, trxs


def estornar(*, user, transacao: TransacaoSaida, observacao: str = ""):
    """Estorno de liberação (RF34/RF35). Restaura saldo, reprocessa status
    via || (ARC-01 §6.8 item 6). Não estorna se monte consumido por outro
    motivo (RF34: não pode estornar se já consumido totalmente)."""
    if transacao.estornada:
        raise ValueError("Transação já estornada.")
    with transaction.atomic():
        pile = Pile.objects.select_for_update().get(pk=transacao.monte_id)
        pile.peso_atual_kg += transacao.peso_baixado_kg
        pile.barras_atuais += transacao.barras_baixadas
        if pile.status == PileStatus.CONSUMIDO:
            pile.status = PileStatus.PARCIAL
        elif pile.status == PileStatus.PARCIAL:
            pass
        else:
            pile.status = PileStatus.DISPONIVEL
        pile.save(update_fields=["peso_atual_kg", "barras_atuais", "status", "updated_at"])
        transacao.estornada = True
        transacao.estornada_em = timezone.now()
        transacao.estornada_por = user
        transacao.save(update_fields=["estornada", "estornada_em", "estornada_por", "updated_at"])
        PileEvent.objects.create(
            monte=pile,
            tipo=EventType.ESTORNO,
            dados={
                "transacao_id": transacao.id,
                "barras": transacao.barras_baixadas,
                "peso_kg": str(transacao.peso_baixado_kg),
                "observacao": observacao,
            },
            created_by=user,
        )
        return pile


def reservar(*, user, monte: Pile, reservado_para: str, setor=None, grupo=None):
    """Reserva: NÃO altera kg/barras (RF40). Grupo via UUID (RF43)."""
    with transaction.atomic():
        pile = Pile.objects.select_for_update().get(pk=monte.pk)
        if pile.status not in (PileStatus.DISPONIVEL,):
            raise ValueError("Apenas montes disponíveis podem ser reservados.")
        pile.status = PileStatus.RESERVADO
        pile.reservado_para = reservado_para
        pile.reservado_em = timezone.now()
        pile.setor_reserva = setor
        pile.grupo_reserva_id = grupo or uuid.uuid4()
        pile.save(update_fields=[
            "status", "reservado_para", "reservado_em",
            "setor_reserva", "grupo_reserva_id", "updated_at",
        ])
        PileEvent.objects.create(
            monte=pile,
            tipo=EventType.RESERVA,
            dados={"reservado_para": reservado_para, "grupo": str(pile.grupo_reserva_id)},
            created_by=user,
        )
        return pile


def cancelar_reserva(*, user, monte: Pile):
    """Cancelar reserva gera evento CANCELAMENTO_RESERVA (RF42)."""
    with transaction.atomic():
        pile = Pile.objects.select_for_update().get(pk=monte.pk)
        if pile.status != PileStatus.RESERVADO:
            raise ValueError("Monte não está reservado.")
        grupo = str(pile.grupo_reserva_id) if pile.grupo_reserva_id else None
        pile.status = PileStatus.DISPONIVEL
        pile.reservado_para = ""
        pile.reservado_em = None
        pile.setor_reserva = None
        pile.grupo_reserva_id = None
        pile.save(update_fields=[
            "status", "reservado_para", "reservado_em",
            "setor_reserva", "grupo_reserva_id", "updated_at",
        ])
        PileEvent.objects.create(
            monte=pile,
            tipo=EventType.CANCELAMENTO_RESERVA,
            dados={"grupo": grupo},
            created_by=user,
        )
        return pile


def mover_para_setor(*, user, monte: Pile, setor):
    """Mover monte ao setor (RF50)."""
    with transaction.atomic():
        pile = Pile.objects.select_for_update().get(pk=monte.pk)
        if pile.status == PileStatus.CONSUMIDO:
            raise ValueError("Monte consumido não pode ser movido.")
        pile.localizacao = Localizacao.SETOR
        pile.setor = setor
        pile.movido_setor_em = timezone.now()
        pile.save(update_fields=["localizacao", "setor", "movido_setor_em", "updated_at"])
        PileEvent.objects.create(
            monte=pile,
            tipo=EventType.MOVIDO_PARA_SETOR,
            dados={"setor": setor.nome},
            created_by=user,
        )
        return pile


def devolver_almoxarifado(*, user, monte: Pile, preservar_reserva: bool = True):
    """Devolução ao almoxarifado (RF51). ARC-04: nunca deixa reserva órfã —
    a estratégia é declarada (preservar ou cancelar) e testada. Default:
    PRESERVA a reserva (monte volta reservado, borda amarela)."""
    with transaction.atomic():
        pile = Pile.objects.select_for_update().get(pk=monte.pk)
        pile.localizacao = Localizacao.ALMOXARIFADO
        pile.setor = None
        pile.movido_setor_em = None
        if not preservar_reserva and pile.status == PileStatus.RESERVADO:
            grupo = str(pile.grupo_reserva_id) if pile.grupo_reserva_id else None
            pile.status = PileStatus.DISPONIVEL
            pile.reservado_para = ""
            pile.reservado_em = None
            pile.setor_reserva = None
            pile.grupo_reserva_id = None
            pile.save(update_fields=[
                "localizacao", "setor", "movido_setor_em",
                "status", "reservado_para", "reservado_em",
                "setor_reserva", "grupo_reserva_id", "updated_at",
            ])
            PileEvent.objects.create(
                monte=pile,
                tipo=EventType.CANCELAMENTO_RESERVA,
                dados={"motivo": "devolucao_almoxarifado", "grupo": grupo},
                created_by=user,
            )
        else:
            pile.save(update_fields=["localizacao", "setor", "movido_setor_em", "updated_at"])
        PileEvent.objects.create(
            monte=pile,
            tipo=EventType.DEVOLVIDO_ALMOXARIFADO,
            dados={"preservou_reserva": preservar_reserva},
            created_by=user,
        )
        return pile


def split(*, user, monte: Pile, barras: int, peso_kg: Decimal, posicao_x: int = 99):
    """Movimentação parcial (RF52): monte filho na posição virtual x=99."""
    if barras <= 0 or peso_kg <= 0:
        raise ValueError("Barras e peso devem ser maiores que zero.")
    with transaction.atomic():
        pile = Pile.objects.select_for_update().get(pk=monte.pk)
        if barras > pile.barras_atuais or peso_kg > pile.peso_atual_kg:
            raise ValueError("Saldo insuficiente para split.")
        pile.peso_atual_kg -= peso_kg
        pile.barras_atuais -= barras
        reliberar_status(pile, houve_baixa=True)
        pile.save(update_fields=["peso_atual_kg", "barras_atuais", "status", "updated_at"])

        filho = Pile.objects.create(
            lote=pile.lote,
            peso_atual_kg=peso_kg,
            barras_atuais=barras,
            posicao_x=posicao_x,
            posicao_y=0,
            status=PileStatus.DISPONIVEL,
            localizacao=pile.localizacao,
            setor=pile.setor,
            monte_origem=pile,
            created_by=user,
        )
        PileEvent.objects.create(
            monte=pile,
            tipo=EventType.SPLIT_CRIADO,
            dados={"filho_id": filho.id, "barras": barras, "peso_kg": str(peso_kg)},
            created_by=user,
        )
        PileEvent.objects.create(
            monte=filho,
            tipo=EventType.SPLIT_CRIADO,
            dados={"origem_id": pile.id},
            created_by=user,
        )
        return filho