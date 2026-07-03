from django.urls import path

from . import views

app_name = "shell"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="home"),
    path("permissoes/", views.ModulePermissionsView.as_view(), name="module_perms"),
]
