"""Minimal URL configuration for tests — avoids importing xhtml2pdf/cairo."""
from django.contrib import admin
from django.urls import path
from usuarios import views as usuarios_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # ROL Consulta
    path('consultas/',                                  usuarios_views.consultas,          name='consultas'),
    path('api/consulta/crear/',                         usuarios_views.crear_consulta,     name='api_crear_consulta'),
    path('api/consulta/<int:consulta_id>/',             usuarios_views.obtener_consulta,   name='api_obtener_consulta'),
    path('api/consulta/editar/<int:consulta_id>/',      usuarios_views.editar_consulta,    name='api_editar_consulta'),
    path('api/consulta/eliminar/<int:consulta_id>/',    usuarios_views.eliminar_consulta,  name='api_eliminar_consulta'),
]
