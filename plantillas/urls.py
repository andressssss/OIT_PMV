from django.urls import path
from plantillas import views

urlpatterns = [
    path('', views.editor, name='plantillas_editor'),
    path('historial/', views.historial, name='plantillas_historial'),
    path('aplicar/', views.aplicar, name='plantillas_aplicar'),
    path('log/', views.log_aplicaciones, name='plantillas_log'),

    # API endpoints
    path('api/nodos/', views.api_obtener_nodos, name='plantillas_api_nodos'),
    path('api/nodo/crear/', views.api_crear_nodo, name='plantillas_api_crear_nodo'),
    path('api/nodo/<int:nodo_id>/editar/', views.api_editar_nodo, name='plantillas_api_editar_nodo'),
    path('api/nodo/<int:nodo_id>/mover/', views.api_mover_nodo, name='plantillas_api_mover_nodo'),
    path('api/nodo/<int:nodo_id>/toggle/', views.api_toggle_nodo, name='plantillas_api_toggle_nodo'),
    path('api/nodo/<int:nodo_id>/visibilidad/', views.api_visibilidad_nodo, name='plantillas_api_visibilidad_nodo'),
    path('api/guardar_version/', views.api_guardar_version, name='plantillas_api_guardar_version'),
    path('api/versiones/', views.api_versiones, name='plantillas_api_versiones'),
    path('api/version/<int:version_id>/snapshot/', views.api_version_snapshot, name='plantillas_api_version_snapshot'),
    path('api/version/<int:version_id>/restaurar/', views.api_restaurar_version, name='plantillas_api_restaurar_version'),
    path('api/preview_aplicar/', views.api_preview_aplicar, name='plantillas_api_preview_aplicar'),
    path('api/ejecutar_aplicar/', views.api_ejecutar_aplicar, name='plantillas_api_ejecutar_aplicar'),
    path('api/log/', views.api_log, name='plantillas_api_log'),
    path('api/cortes/', views.api_cortes, name='plantillas_api_cortes'),
]
