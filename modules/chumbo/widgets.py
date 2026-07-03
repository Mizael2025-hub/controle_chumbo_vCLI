from django.db.models import Sum
from django.urls import reverse

from modules.chumbo.ligas.models import Liga
from modules.chumbo.montes.models import Pile


def saldo_por_liga_widget(request):
    """Saldo por liga na home agregada. ARC-15: mostra todas as ligas
    (com scroll), nunca corta em um número fixo."""
    ligas = Liga.objects.filter(is_active=True).order_by("sort_order", "id")
    if not ligas.exists():
        return {
            "title": "Controle de Chumbo",
            "html": "<p class='muted'>Nenhuma liga cadastrada.</p>",
        }
    rows = []
    for l in ligas:
        agg = Pile.objects.filter(
            lote__liga=l, lote__is_active=True, is_active=True
        ).aggregate(k=Sum("peso_atual_kg"), b=Sum("barras_atuais"))
        kg = agg["k"] or 0
        barras = agg["b"] or 0
        cor = l.chave_cor
        rows.append(
            f"<a class='liga-row' href='{reverse('chumbo:estoque')}'>"
            f"<span class='liga-dot liga-{cor}'></span>"
            f"<span>{l.nome}</span><b>{float(kg):.3f} kg</b>"
            f"<small>{barras}b</small></a>"
        )
    return {
        "title": "Saldo por liga",
        "html": f"<div class='liga-list'>{''.join(rows)}</div>",
    }