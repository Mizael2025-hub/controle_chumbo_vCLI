"""Registry central de módulos.

Preenchido no `AppConfig.ready()` de cada módulo via `register(MANIFEST)`.
Lido pelo `shell` (menu dinâmico + dashboard agregada) e por `base.mixins`.
"""

_REGISTRY = []


def register(manifest):
    """Registra um ModuleManifest (idempotente, ordenado por `order`)."""
    existing = {m.slug for m in _REGISTRY}
    if manifest.slug in existing:
        return
    _REGISTRY.append(manifest)
    _REGISTRY.sort(key=lambda m: m.order)


def all_manifests():
    return list(_REGISTRY)


def get(slug):
    for m in _REGISTRY:
        if m.slug == slug:
            return m
    return None


def slugs():
    return [m.slug for m in _REGISTRY]


def visible_for(user):
    """Manifests que o usuário pode acessar (admin global vê todos)."""
    if not user.is_authenticated:
        return []
    if user.is_superuser or getattr(user, "role", None) == "admin":
        return all_manifests()
    out = []
    for m in all_manifests():
        if user.has_module_role(m.slug, "operador") or user.has_module_role(m.slug, "admin"):
            out.append(m)
    return out
