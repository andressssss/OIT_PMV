from django.urls import path, include
from api.views.dashboard import DashboardKpisView, DashboardFichasView, UsuariosPorRolView, DashboardRapsView

urlpatterns = [
  path("kpis/", DashboardKpisView.as_view(), name="dashboard-kpis"),
  path("fichas/", DashboardFichasView.as_view(), name="dashboard-fichas"),
  path("usuarios-rol/", UsuariosPorRolView.as_view(), name="dashboard-usuarios-rol"),
  path("juicios/", DashboardRapsView.as_view(), name="dashboard-juicios"),
]