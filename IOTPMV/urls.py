"""
URL configuration for IOTPMV project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from tasks import views as tasks_views
from usuarios import views as usuarios_views
from formacion import views as formacion_views
from matricula import views as matricula_views
from gestion_instructores import views as gestion_instructores_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Ruta Admin
    path('admin/', admin.site.urls),

    # Ruta default
    path('', usuarios_views.home, name='home'),

    # Registro usuarios
    path('signup/', usuarios_views.signup, name='signup'),

    # Log out
    path('logout/', usuarios_views.signout, name='logout'),

    # Log In
    path('signin/', usuarios_views.signin, name='signin'),

    # CRUD base TASKS:
    path('tasks/', tasks_views.tasksView, name='tasks'),
    path('tasks_completed/', tasks_views.tasks_completed, name='tasks_completed'),
    path('tasks/create/', tasks_views.create_task, name='create_task'),
    path('tasks/<int:task_id>/', tasks_views.task_detail, name='task_detail'),
    path('tasks/<int:task_id>/complete/',
         tasks_views.complete_task, name='complete_task'),
    path('tasks/<int:task_id>/delete/',
         tasks_views.delete_task, name='delete_task'),

    # ROL Admin
    path('admin_dashboard/', usuarios_views.dashboard_admin, name='admin_dashboard'),
    path('aprendices/', usuarios_views.aprendices, name='aprendices'),
    path('aprendices/crear/', usuarios_views.crear_aprendices,
         name='crear_aprendices'),  # ----> Crear aprendiz
    path('aprendices/<int:aprendiz_id>/', usuarios_views.detalle_aprendices,
         name='obtener_detalles_aprendiz'),  # ----> actualizar informacion de aprendiz
    path('aprendices/<int:aprendiz_id>/eliminar', usuarios_views.eliminar_aprendiz,
         name='eliminar_aprendiz'),  # ----> Eliminar informacion de aprendiz
    path('instructores/', usuarios_views.instructores, name='instructores'),
    path('instructores/crear/', usuarios_views.crear_instructor,
         name='crear_instructor'),
    path('instructores/<int:instructor_id>/',
         usuarios_views.instructor_detalle, name='instructor_detalle'),
    path('obtener_detalles/<int:instructor_id>/',
         usuarios_views.instructor_detalle_tabla, name='obtener_detalles'),
    path('administradores/', usuarios_views.administradores, name='administradores'),
    path('administradores/crear/', usuarios_views.crear_administradores,
         name='crear_administradores'),  # ----> Crear nuevo usuario admin
    path('administradores/<int:admin_id>/', usuarios_views.detalle_administradores,
         name='administrador_detalle'),  # ----> actualizar info usuario admin
    path('obtener_detalles/<int:admin_id>/', usuarios_views.administrador_detalle_tabla,
         name='obtener_detalles_admin'),
    path('administradores/<int:admin_id>/eliminar', usuarios_views.eliminar_admin,
         name='eliminar_administrador'),  # ----> Eliminar info usuario admin

    # ROL Lideres
    path('lideres/', usuarios_views.lideres, name='lideres'),
    path('lideres/crear/', usuarios_views.crear_lideres, name='crear_lideres'),
    path('lideres/<int:lider_id>/',
         usuarios_views.detalle_lideres, name='detalle_lider'),
    path('lideres/<int:lider_id>/eliminar',
         usuarios_views.eliminar_lideres, name='eliminar_lider'),

    # ROL Departamentos
    path('departamentos/', usuarios_views.departamentos, name='departamentos'),
    path('departamentos/crear/', usuarios_views.creardepartamentos,
         name='creardepartamentos'),
    path('departamentos/<int:departamento_id>/', usuarios_views.detalle_departamentos,
         name='detalle_departamentos'),
    path('departamentos/<int:departamento_id>/eliminar', usuarios_views.eliminar_departamentos,
         name='eliminar_departamentos'),

    # ROL Municipios
    path('municipios/', usuarios_views.municipios, name='municipios'),
    path('municipios/crear/', usuarios_views.crearmunicipios, name='crearmunicipios'),
    path('municipios/<int:municipio_id>/',
         usuarios_views.detalle_municipios, name='detalle_municipio'),
    path('municipios/<int:municipio_id>/eliminar/', usuarios_views.eliminar_municipios, name='eliminar_municipio'),
    path('obtener-municipios/', usuarios_views.obtener_municipios, name='obtener_municipios'),

    # ROL Instituciones
    path('instituciones/', usuarios_views.instituciones,
         name='instituciones'),
    path('instituciones/crear/', usuarios_views.crear_instituciones,
         name='crear_instituciones'),
    path('instituciones/<int:institucion_id>/', usuarios_views.detalle_instituciones,
         name='detalle_institucion'),
    path('instituciones/<int:institucion_id>/eliminar/', usuarios_views.eliminar_instituciones,
         name='eliminar_institucion'),

    # Rol  De Centros De Formacion
    path('centroformacion/', usuarios_views.centrosformacion,
         name='centrosformacion'),
    path('centroformacion/crear/', usuarios_views.crear_centrosformacion,
         name='crear_centrosformacion'),
    path('centroformacion/<int:centroformacion_id>/', usuarios_views.detalle_centrosformacion,
         name='detalle_centrosformacion'),
    path('centroformacion/<int:centroformacion_id>/eliminar/', usuarios_views.eliminar_centrosformacion,
         name='eliminar_centrosformacion'),


    # ROL Representantes Legales
    path('represantesLegales/', usuarios_views.representante_legal,
         name='represantesLegales'),
    path('represantesLegales/crear/', usuarios_views.crear_representante_legal,
         name='crearRepresantesLegales'),
    path('represantesLegales/<int:repreLegal_id>/', usuarios_views.detalle_representante_legal,
         name='detalleRepresanteLegal'),
    path('represantesLegales/<int:repreLegal_id>/eliminar', usuarios_views.eliminar_representante_legal,
         name='eliminarRepresanteLegal'),

    # ROL Instructores
    path('gestion_instructor/', gestion_instructores_views.gestion_instructor,
         name='gestion_instructor'),
    path('get_tree_instructor/', formacion_views.tree_detalle,
         name='get_tree_instructor'),

    # Panel instructor
    path('fichas/', formacion_views.listar_fichas, name='listar_fichas'),
    path('fichas/<int:ficha_id>/', formacion_views.panel_ficha, name='panel_ficha'),
    path('fichas/<int:ficha_id>/crear_actividad/', formacion_views.crear_actividad, name='crear_actividad'),
    path('fichas/<int:ficha_id>/crear_encuentro/', formacion_views.crear_encuentro, name='crear_encuentro'),

    # ROL Aprendices
    path('panel_aprendiz/', formacion_views.panel_aprendiz, name='panel_aprendiz'),




    # Novedades
    path('novedades/', usuarios_views.novedades, name='novedades'),
    path('novedades/crear/', usuarios_views.crear_novedad , name='crear_novedad'),

    # Fichas
    path('fichas_adm/', formacion_views.listar_fichas_adm, name='fichas_adm'), 
    path('fichas_adm/crear/', formacion_views.crear_ficha, name='fichas_adm_crear'), 

    # Programas
    path('programas/', formacion_views.listar_programas, name='programas'),
    path('programas/crear/', formacion_views.crear_programa, name='crear_programas'),

    # Competencias
    path('competencias/', formacion_views.listar_competencias, name='competencias'),
    path('competencias/crear/', formacion_views.crear_competencias,
         name='crear_competencias'),

    # Raps
    path('raps/', formacion_views.listar_raps, name = 'raps'),
    path('raps/crear/', formacion_views.crear_raps, name='crear_raps'),

    # Tree
    path('api/carpetas/<int:ficha_id>/', formacion_views.obtener_carpetas, name='obtener_carpetas'),
    path('api/carpetas/<int:ficha_id>/<int:aprendiz_id>', formacion_views.obtener_carpetas_aprendiz, name='obtener_carpetas_aprendiz'),
    path('prueba_tree/', formacion_views.prueba_tree, name='prueba_tree'),
    path('fichas/<int:ficha_id>/cargar_documento/', formacion_views.cargar_documento, name='cargar_documento'),
    path('fichas/<int:ficha_id>/<str:carpeta>/cargar_link_folders/', formacion_views.cargar_link_folders, name='cargar_link_folders'),
    path('api/estudiantes/<int:ficha_id>/', formacion_views.listar_estudiantes, name='listar_estudiantes'),

    # Eliminar documentos
    path('eliminar_documento/<int:documento_id>/', formacion_views.eliminar_doc, name='eliminar_documento'),

    # Pre matricula
    path('pre_matricula/', matricula_views.fichas_prematricula, name='pre_matricula'),
    path('asignar_aprendices/<int:ficha_id>/', matricula_views.asignar_aprendices, name='asignar_aprendices'),
    path('confirmar_documentacion/<int:ficha_id>/', matricula_views.confirmar_documentacion, name='confirmar_documentacion'),
    path('subir_documento_prematricula/<int:documento_id>/', formacion_views.cargar_documento_prematricula, name='subir_documento_prematricula'),
    path('pre_matricula/<int:ficha_id>/detalle/', matricula_views.ver_docs_prematricula_ficha, name='ver_docs_prematricula'),

     path('cargar_aprendices_masivo/', usuarios_views.cargar_aprendices_masivo, name='cargar_aprendices_masivo'),
    path('descargar_documentos_zip/<int:aprendiz_id>/', matricula_views.descargar_documentos_zip, name='descargar_documentos_zip'),
    path('confirmar_documento/<int:documento_id>/<int:ficha_id>/', matricula_views.confirmar_documento, name='confirmar_documento'),


]       

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
