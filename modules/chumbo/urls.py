from django.urls import include, path

from . import views

app_name = "chumbo"

urlpatterns = [
    path("", views.ChumboHomeView.as_view(), name="home"),
    path("ligas/", include("modules.chumbo.ligas.urls")),
    path("destinos/", include("modules.chumbo.destinos.urls")),
    path("modelos/", include("modules.chumbo.modelos.urls")),
    path("lotes/", include("modules.chumbo.lotes.urls")),
]