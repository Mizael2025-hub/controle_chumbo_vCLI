from django.views.generic import TemplateView

from base.mixins import ModulePermMixin


class ChumboHomeView(ModulePermMixin, TemplateView):
    template_name = "chumbo/home.html"
    module_slug = "chumbo"
    required_module_role = ("operador", "admin")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from modules.registry import get

        ctx["manifest"] = get("chumbo")
        return ctx
