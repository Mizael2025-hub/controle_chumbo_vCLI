from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path("admin/dj-celery-panel/", include("dj_celery_panel.urls")),
    path("admin/", admin.site.urls),
    path("health/", views.health, name="health"),
    path("manifest.json", views.manifest_json, name="manifest_json"),
    path("sw.js", views.service_worker, name="service_worker"),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("cadastros/", include("shared.urls", namespace="shared")),
    path("chumbo/", include("modules.chumbo.urls", namespace="chumbo")),
    path("", include("shell.urls", namespace="shell")),
]
