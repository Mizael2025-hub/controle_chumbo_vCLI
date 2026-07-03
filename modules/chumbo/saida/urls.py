from django.urls import path

from . import views

urlpatterns = [
    path("liberar/", views.LiberacaoView.as_view(), name="liberacao"),
    path("liberar/historico/", views.LiberacaoHistoricoView.as_view(), name="liberacao_hist"),
    path("liberar/<int:pk>/estornar/", views.EstornoView.as_view(), name="estornar"),
]