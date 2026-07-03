from django.urls import path

from . import views

urlpatterns = [
    path("novo/", views.LoteStep1View.as_view(), name="lote_create"),
    path("novo/grade/", views.LoteStep2View.as_view(), name="lote_step2"),
    path("estoque/", views.EstoqueListView.as_view(), name="estoque"),
    path("estoque/<int:pk>/", views.EstoqueGradeView.as_view(), name="estoque_lote"),
]