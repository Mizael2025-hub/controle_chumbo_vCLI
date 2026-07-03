from importlib import import_module

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, TemplateView

from base.mixins import RoleRequiredMixin
from modules.registry import visible_for


def _load_widgets(request, manifests):
    """Agrega widgets de dashboard de cada módulo (caminho dotted → callable).

    O callable recebe `request` e retorna um dict {'title','html'} ou None.
    Falhas de import/execução são silenciadas (módulo ausente não quebra a home).
    """
    widgets = []
    for manifest in manifests:
        for path in manifest.dashboard_widgets:
            try:
                module_path, func_name = path.rsplit(".", 1)
                fn = getattr(import_module(module_path), func_name)
            except Exception:
                continue
            try:
                result = fn(request)
            except Exception:
                continue
            if result:
                widgets.append(result)
    return widgets


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "shell/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["modules"] = visible_for(self.request.user)
        ctx["widgets"] = _load_widgets(self.request, ctx["modules"])
        return ctx


class ModulePermissionsView(RoleRequiredMixin, ListView):
    template_name = "shell/module_perms.html"
    context_object_name = "users"
    model = get_user_model()
    allowed_roles = ("admin",)
    paginate_by = 25

    def get_queryset(self):
        return get_user_model().objects.order_by("name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from modules.registry import slugs
        ctx["module_slugs"] = slugs()
        return ctx
