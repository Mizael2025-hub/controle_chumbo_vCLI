from modules.chumbo.ligas.models import Liga


def saldo_por_liga_widget(request):
    """Widget p/ a home agregada do shell. Sprint 2: mostra ligas (saldo 0 kg
    ainda sem lotes/montes — vira real no Sprint 3). ARC-15: mostra todas."""
    ligas = Liga.objects.filter(is_active=True).order_by("sort_order", "id")
    if not ligas.exists():
        return {"title": "Controle de Chumbo", "html": "<p class='muted'>Nenhuma liga cadastrada.</p>"}
    rows = "".join(
        f"<div class='row'><span>{l.nome}</span><b>0 kg</b></div>" for l in ligas
    )
    return {"title": "Saldo por liga", "html": f"<div class='liga-list'>{rows}</div>"}
