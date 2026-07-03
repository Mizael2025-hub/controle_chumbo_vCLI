from django.utils.text import slugify

from .models import Maquina, Operador, Setor, Turno


def seed_shared():
    """Popula cadastros shared de referência (idempotente)."""
    setores_data = [
        ("Almoxarifado", "producao"),
        ("Produção", "producao"),
        ("Saída Direta", "saida_direta"),
    ]
    setores = {}
    for nome, tipo in setores_data:
        obj, _ = Setor.objects.get_or_create(
            slug=slugify(nome),
            defaults={"nome": nome, "tipo": tipo},
        )
        setores[nome] = obj

    turnos_data = ["Manhã", "Tarde", "Noite"]
    for nome in turnos_data:
        Turno.objects.get_or_create(nome=nome, defaults={"sort_order": turnos_data.index(nome)})

    operadores_data = ["João Silva", "Maria Santos", "Carlos Pereira", "Ana Oliveira"]
    for i, nome in enumerate(operadores_data):
        Operador.objects.get_or_create(nome=nome, defaults={"sort_order": i})

    maquinas_data = [
        ("Máquina 01", "Produção"),
        ("Máquina 02", "Produção"),
        ("Máquina 03", "Produção"),
    ]
    for i, (nome, setor_nome) in enumerate(maquinas_data):
        Maquina.objects.get_or_create(
            nome=nome,
            defaults={"setor": setores[setor_nome], "sort_order": i},
        )

    return {
        "setores": Setor.objects.count(),
        "operadores": Operador.objects.count(),
        "turnos": Turno.objects.count(),
        "maquinas": Maquina.objects.count(),
    }
