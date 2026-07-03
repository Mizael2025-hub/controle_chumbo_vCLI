from django.urls import path

from . import views

urlpatterns = [
    path("", views.LigaList.as_view(), name="ligas_list"),
    path("novo/", views.LigaCreate.as_view(), name="ligas_create"),
    path("<int:pk>/editar/", views.LigaUpdate.as_view(), name="ligas_update"),
    path("<int:pk>/excluir/", views.LigaDelete.as_view(), name="ligas_delete"),
]
