from django.urls import path

from . import views

urlpatterns = [
    path("", views.DestinoList.as_view(), name="destinos_list"),
    path("novo/", views.DestinoCreate.as_view(), name="destinos_create"),
    path("<int:pk>/editar/", views.DestinoUpdate.as_view(), name="destinos_update"),
    path("<int:pk>/excluir/", views.DestinoDelete.as_view(), name="destinos_delete"),
]
