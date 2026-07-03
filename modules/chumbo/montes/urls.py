from django.urls import path

from . import views

urlpatterns = [
    path("reservar/<int:pk>/", views.ReservaView.as_view(), name="reservar_create"),
    path("reservar/<int:pk>/cancelar/", views.CancelarReservaView.as_view(), name="reservar_cancel"),
    path("mover/<int:pk>/", views.MoverView.as_view(), name="mover"),
    path("mover/<int:pk>/devolver/", views.DevolverView.as_view(), name="devolver"),
    path("mover/<int:pk>/split/", views.SplitView.as_view(), name="split"),
    path("eventos/<int:pk>/", views.EventosView.as_view(), name="eventos"),
    path("remanejar/<int:pk>/", views.RemanejarView.as_view(), name="remanejar"),
]