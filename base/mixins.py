from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class RoleRequiredMixin(LoginRequiredMixin):
    """Bloqueia mutations sensíveis: só roles em `allowed_roles` (ou admin global)."""

    allowed_roles = ("admin",)

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return self.handle_no_permission()
        if user.is_admin or getattr(user, "role", None) in self.allowed_roles:
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied


class PerPageMixin:
    """Paginação ajustável via ?per_page=."""

    per_page = 25

    def get_paginate_by(self, queryset=None):
        try:
            return int(self.request.GET.get("per_page", self.per_page))
        except (TypeError, ValueError):
            return self.per_page


class ModulePermMixin(LoginRequiredMixin):
    """Checa permissão do usuário no módulo (request.module ou module_slug).

    Admin global (is_admin) sempre passa. `required_module_role` aceita str ou
    tuple de roles válidas dentro do módulo (ex.: ("operador","admin") p/ leitura).
    """

    required_module_role = "admin"
    module_slug = None

    def get_module_slug(self):
        return self.module_slug or getattr(self.request, "module", None)

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return self.handle_no_permission()
        if user.is_admin:
            return super().dispatch(request, *args, **kwargs)
        slug = self.get_module_slug()
        roles = self.required_module_role
        if isinstance(roles, str):
            roles = (roles,)
        if slug and any(user.has_module_role(slug, r) for r in roles):
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied
