from django.urls import path
from rest_framework.routers import DefaultRouter
from api.views.dashboard import (
    DashboardKpisView, DashboardFichasView,
    UsuariosPorRolView, DashboardRapsView, NovedadesViewSet
)
from api.views.dashboard_instructores import (
    DashboardInstructoresView, DashboardInstructoresExportView,
    InstructorDetalleView, AprendicesMayoriaEdadView,
)

router = DefaultRouter()
router.register(r'novedades', NovedadesViewSet, basename='novedades')

urlpatterns = [
    path("kpis/", DashboardKpisView.as_view(), name="dashboard-kpis"),
    path("fichas/", DashboardFichasView.as_view(), name="dashboard-fichas"),
    path("usuarios-rol/", UsuariosPorRolView.as_view(), name="dashboard-usuarios-rol"),
    path("juicios/", DashboardRapsView.as_view(), name="dashboard-juicios"),
    path("instructores/", DashboardInstructoresView.as_view(), name="dashboard-instructores"),
    path("instructores/exportar/", DashboardInstructoresExportView.as_view(), name="dashboard-instructores-export"),
    path("instructores/<int:instructor_id>/", InstructorDetalleView.as_view(), name="dashboard-instructor-detalle"),
    path("aprendices-mayoria-edad/", AprendicesMayoriaEdadView.as_view(), name="dashboard-aprendices-mayoria-edad"),
] + router.urls
