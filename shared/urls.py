from django.urls import path

from . import views

app_name = "shared"

urlpatterns = []
for _slug, (List, Create, Update, Delete) in views.CRUD.items():
    plural = List.plural
    urlpatterns += [
        path(f"{plural}/", List.as_view(), name=f"{_slug}_list"),
        path(f"{plural}/novo/", Create.as_view(), name=f"{_slug}_create"),
        path(f"{plural}/<int:pk>/editar/", Update.as_view(), name=f"{_slug}_update"),
        path(f"{plural}/<int:pk>/excluir/", Delete.as_view(), name=f"{_slug}_delete"),
    ]
