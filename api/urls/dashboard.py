from django.urls import path
from rest_framework.routers import DefaultRouter
from api.views.dashboard import (
    DashboardKpisView, DashboardFichasView,
    UsuariosPorRolView, DashboardRapsView, NovedadesViewSet
)

router = DefaultRouter()
router.register(r'novedades', NovedadesViewSet, basename='novedades')

urlpatterns = [
    path("kpis/", DashboardKpisView.as_view(), name="dashboard-kpis"),
    path("fichas/", DashboardFichasView.as_view(), name="dashboard-fichas"),
    path("usuarios-rol/", UsuariosPorRolView.as_view(), name="dashboard-usuarios-rol"),
    path("juicios/", DashboardRapsView.as_view(), name="dashboard-juicios"),
] + router.urls
