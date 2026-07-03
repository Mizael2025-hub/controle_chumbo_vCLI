from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from base.mixins import ModulePermMixin


class _List(ModulePermMixin, ListView):
    template_name = "shared/list.html"
    context_object_name = "objects"
    required_module_role = "admin"
    module_slug = "chumbo"
    list_fields = ()
    slug = ""
    title = ""

    def get_queryset(self):
        return self.model.objects.filter(is_active=True).order_by("sort_order", "id")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["fields"] = self.list_fields
        ctx["slug"] = self.slug
        ctx["title"] = self.title
        ctx["create_url"] = reverse_lazy(f"chumbo:{self.slug}_create")
        ctx["update_url_name"] = f"chumbo:{self.slug}_update"
        ctx["delete_url_name"] = f"chumbo:{self.slug}_delete"
        return ctx


class _Create(ModulePermMixin, CreateView):
    template_name = "shared/form.html"
    required_module_role = "admin"
    module_slug = "chumbo"
    slug = ""

    def get_success_url(self):
        return reverse_lazy(f"chumbo:{self.slug}_list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["slug"] = self.slug
        ctx["title"] = f"Novo {self.model._meta.verbose_name}"
        ctx["list_url"] = reverse_lazy(f"chumbo:{self.slug}_list")
        return ctx


class _Update(ModulePermMixin, UpdateView):
    template_name = "shared/form.html"
    required_module_role = "admin"
    module_slug = "chumbo"
    slug = ""

    def get_success_url(self):
        return reverse_lazy(f"chumbo:{self.slug}_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["slug"] = self.slug
        ctx["title"] = f"Editar {self.model._meta.verbose_name}"
        ctx["list_url"] = reverse_lazy(f"chumbo:{self.slug}_list")
        return ctx


class _Delete(ModulePermMixin, DeleteView):
    template_name = "shared/confirm_delete.html"
    required_module_role = "admin"
    module_slug = "chumbo"
    slug = ""

    def get_success_url(self):
        return reverse_lazy(f"chumbo:{self.slug}_list")

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
        ctx["list_url"] = reverse_lazy(f"chumbo:{self.slug}_list")
        return ctx


def make(model, form_class, slug, title, list_fields):
    """Factory de CRUD para um cadastro do módulo Chumbo."""
    List = type(
        f"{slug.title()}List",
        (_List,),
        {"model": model, "slug": slug, "title": title, "list_fields": list_fields},
    )
    Create = type(
        f"{slug.title()}Create",
        (_Create,),
        {"model": model, "form_class": form_class, "slug": slug},
    )
    Update = type(
        f"{slug.title()}Update",
        (_Update,),
        {"model": model, "form_class": form_class, "slug": slug},
    )
    Delete = type(f"{slug.title()}Delete", (_Delete,), {"model": model, "slug": slug})
    return List, Create, Update, Delete
