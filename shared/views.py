from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from base.mixins import RoleRequiredMixin
from .forms import MaquinaForm, OperadorForm, SetorForm, TurnoForm
from .models import Maquina, Operador, Setor, Turno


class _CRUDList(RoleRequiredMixin, ListView):
    template_name = "shared/list.html"
    context_object_name = "objects"
    allowed_roles = ("admin",)
    list_fields = ()
    slug = ""
    plural = ""
    title = ""

    def get_queryset(self):
        return self.model.objects.filter(is_active=True).order_by("sort_order", "id")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["fields"] = self.list_fields
        ctx["slug"] = self.slug
        ctx["title"] = self.title
        ctx["create_url"] = reverse_lazy(f"shared:{self.slug}_create")
        ctx["update_url_name"] = f"shared:{self.slug}_update"
        ctx["delete_url_name"] = f"shared:{self.slug}_delete"
        return ctx


class _CRUDCreate(RoleRequiredMixin, CreateView):
    template_name = "shared/form.html"
    allowed_roles = ("admin",)
    slug = ""

    def get_success_url(self):
        return reverse_lazy(f"shared:{self.slug}_list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["slug"] = self.slug
        ctx["title"] = f"Novo {self.model._meta.verbose_name}"
        ctx["list_url"] = reverse_lazy(f"shared:{self.slug}_list")
        return ctx


class _CRUDUpdate(RoleRequiredMixin, UpdateView):
    template_name = "shared/form.html"
    allowed_roles = ("admin",)
    slug = ""

    def get_success_url(self):
        return reverse_lazy(f"shared:{self.slug}_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["slug"] = self.slug
        ctx["title"] = f"Editar {self.model._meta.verbose_name}"
        ctx["list_url"] = reverse_lazy(f"shared:{self.slug}_list")
        return ctx


class _CRUDDelete(RoleRequiredMixin, DeleteView):
    template_name = "shared/confirm_delete.html"
    allowed_roles = ("admin",)
    slug = ""

    def get_success_url(self):
        return reverse_lazy(f"shared:{self.slug}_list")

    def form_valid(self, form):
        self.object = self.get_object()
        self.object.is_active = False
        self.object.save(update_fields=["is_active", "updated_at"])
        if self.request.headers.get("HX-Request") or self.request.META.get("HTTP_HX_REQUEST"):
            return HttpResponse(status=204)
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["slug"] = self.slug
        ctx["list_url"] = reverse_lazy(f"shared:{self.slug}_list")
        return ctx


def _make(model, form_class, slug, plural, title, list_fields):
    List = type(
        f"{slug.title()}ListView",
        (_CRUDList,),
        {"model": model, "slug": slug, "plural": plural, "title": title, "list_fields": list_fields},
    )
    Create = type(
        f"{slug.title()}CreateView",
        (_CRUDCreate,),
        {"model": model, "form_class": form_class, "slug": slug},
    )
    Update = type(
        f"{slug.title()}UpdateView",
        (_CRUDUpdate,),
        {"model": model, "form_class": form_class, "slug": slug},
    )
    Delete = type(
        f"{slug.title()}DeleteView",
        (_CRUDDelete,),
        {"model": model, "slug": slug},
    )
    return List, Create, Update, Delete


CRUD = {
    "setor": _make(Setor, SetorForm, "setor", "setores", "Setores", ["nome", "tipo", "sort_order"]),
    "operador": _make(Operador, OperadorForm, "operador", "operadores", "Operadores", ["nome", "sort_order"]),
    "turno": _make(Turno, TurnoForm, "turno", "turnos", "Turnos", ["nome", "sort_order"]),
    "maquina": _make(Maquina, MaquinaForm, "maquina", "maquinas", "Máquinas", ["nome", "setor", "sort_order"]),
}
