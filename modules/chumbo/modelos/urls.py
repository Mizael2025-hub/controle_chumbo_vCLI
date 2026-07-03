from django.urls import path

from . import views

urlpatterns = [
    path("", views.ModeloList.as_view(), name="modelos_list"),
    path("novo/", views.ModeloCreate.as_view(), name="modelos_create"),
    path("<int:pk>/editar/", views.ModeloUpdate.as_view(), name="modelos_update"),
    path("<int:pk>/excluir/", views.ModeloDelete.as_view(), name="modelos_delete"),
]
