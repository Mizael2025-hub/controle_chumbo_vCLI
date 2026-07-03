def module_menu(request):
    """Injeta menu dinâmico: só módulos visíveis ao usuário (§2.4).
    Retorna dicts {label, url_name, items} com a menu_for(user) já filtrada
    (templates não chamam métodos com argumentos)."""
    if not hasattr(request, "user") or not request.user.is_authenticated:
        return {"module_menu": []}
    try:
        from modules.registry import visible_for

        manifests = visible_for(request.user)
    except Exception:
        manifests = []
    menu = []
    for m in manifests:
        menu.append(
            {
                "label": m.label,
                "url_name": m.url_name,
                "items": m.menu_for(request.user),
            }
        )
    return {"module_menu": menu}
