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
from django.urls import path, include
from tasks import views as tasks_views
from usuarios import views as usuarios_views
from formacion import views as formacion_views
from matricula import views as matricula_views
from administracion import views as admin_views
from gestion_instructores import views as gestion_instructores_views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Ruta Admin
    path('admin/', admin.site.urls),

    # Ruta default
    path('', usuarios_views.home, name='home'),

    # Registro usuarios
    path('signup/', usuarios_views.signup, name='signup'),

    # Log out
    path('logout/', usuarios_views.signout, name='logout'),
    path('api/check-auth/', usuarios_views.check_authentication, name='check-auth'),

    # Log In
    path('signin/', usuarios_views.signin, name='signin'),
    
    # Perfil
    path('perfil/', usuarios_views.perfil, name='perfil'),
    path('editar_perfil/', usuarios_views.editar_perfil, name='editar_perfil'),

    # Eliminar documento
    path('eliminar_documentoinstru/<int:hv_id>/', usuarios_views.eliminar_documentoinstru, name='eliminar_documentoinstru'),
    
    # Recuperacion de contraseña

    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),


    # CRUD base TASKS:
    path('tasks/', tasks_views.tasksView, name='tasks'),
    path('tasks_completed/', tasks_views.tasks_completed, name='tasks_completed'),
    path('tasks/create/', tasks_views.create_task, name='create_task'),
    path('tasks/<int:task_id>/', tasks_views.task_detail, name='task_detail'),
    path('tasks/<int:task_id>/complete/',tasks_views.complete_task, name='complete_task'),
    path('tasks/<int:task_id>/delete/',tasks_views.delete_task, name='delete_task'),

    # ROL Admin
    # Aprendices
    path('admin_dashboard/', usuarios_views.dashboard_admin, name='admin_dashboard'),
    path('aprendices/', usuarios_views.aprendices, name='aprendices'),
    path('aprendices/crear/', usuarios_views.crear_aprendices,name='crear_aprendices'),  # ----> Crear aprendiz
    # path('aprendices/<int:aprendiz_id>/', usuarios_views.detalle_aprendices,name='obtener_detalles_aprendiz'),  # ----> actualizar informacion de aprendiz
    path('aprendices/<int:aprendiz_id>/eliminar', usuarios_views.eliminar_aprendiz,name='eliminar_aprendiz'),  # ----> Eliminar informacion de aprendiz
    path('aprendices/editar/<int:id>/', usuarios_views.editar_aprendiz, name='editar_aprendiz'),

    # API llenado de filtros
    path('api/aprendices/usuarios_crea/', usuarios_views.obtener_usuarios_creacion, name='api_usuarios_crea_aprendices'),
    path('api/aprendices/estados/', usuarios_views.obtener_opciones_estados, name='api_estados_aprendices'),

    # API filtrado de aprendices

    path('api/aprendices/filtrar-aprendices/', usuarios_views.filtrar_aprendices, name='api_filtrar_aprendices'),


    # Instructores
    
    path('instructores/', usuarios_views.instructores, name='instructores'),
    path('instructores/crear/', usuarios_views.crear_instructor,name='crear_instructor'),
    path('instructores/<int:instructor_id>/',usuarios_views.instructor_detalle, name='instructor_detalle'),
    path('obtener_detalles/<int:instructor_id>/',usuarios_views.instructor_detalle_tabla, name='obtener_detalles'),
    
    # Rol Administradores
    path('administradores/', usuarios_views.administradores, name='administradores'),
    path('administradores/crear/', usuarios_views.crear_administradores,name='crear_administradores'),  # ----> Crear nuevo usuario admin
    path('administradores/<int:admin_id>/', usuarios_views.detalle_administradores,name='administrador_detalle'),  # ----> actualizar info usuario admin
    path('obtener_detalles/<int:admin_id>/', usuarios_views.administrador_detalle_tabla, name='obtener_detalles_admin'),
    path('administradores/<int:admin_id>/eliminar', usuarios_views.eliminar_admin, name='eliminar_administrador'),  # ----> Eliminar info usuario admin
    
    # ROL Gestores
    path('gestores/', usuarios_views.gestores, name='gestores'),
    path('gestores/crear/', usuarios_views.crear_gestor, name='crear_gestor'),  # ----> Crear nuevo usuario gestor
    path('gestores/<int:gestor_id>/', usuarios_views.gestor_detalle, name='gestor_detalle'), 

    # ROL Cuentas
    path('cuentas/', usuarios_views.cuentas, name='cuentas'),
    path('cuentas/crear/', usuarios_views.crear_pcuentas, name='crear_pcuentas'),
    path('cuentas/<int:cuentas_id>/', usuarios_views.cuentas_detalle, name='cuentas_detalle'),

    # ROL Lideres
    path('lideres/', usuarios_views.lideres, name='lideres'),
    path('lideres/crear/', usuarios_views.crear_lideres, name='crear_lideres'),
    path('lideres/<int:lider_id>/',usuarios_views.detalle_lideres, name='detalle_lider'),
    path('lideres/<int:lider_id>/eliminar',usuarios_views.eliminar_lideres, name='eliminar_lider'),

    # ROL Departamentos
    path('departamentos/', usuarios_views.departamentos, name='departamentos'),
    path('departamentos/crear/', usuarios_views.creardepartamentos, name='creardepartamentos'),
    path('departamentos/<int:departamento_id>/', usuarios_views.detalle_departamentos,name='detalle_departamentos'),
    path('departamentos/<int:departamento_id>/eliminar', usuarios_views.eliminar_departamentos,name='eliminar_departamentos'),

    # ROL Municipios
    path('municipios/', usuarios_views.municipios, name='municipios'),
    path('municipios/crear/', usuarios_views.crearmunicipios, name='crearmunicipios'),
    path('municipios/<int:municipio_id>/',usuarios_views.detalle_municipios, name='detalle_municipio'),
    path('municipios/<int:municipio_id>/eliminar/', usuarios_views.eliminar_municipios, name='eliminar_municipio'),
    
    # Endpoint municipio
    path('api/municipiosFormInsti/', usuarios_views.obtener_municipios, name='api_municipios_form_insti'),

    # ROL Instituciones
    path('instituciones/', usuarios_views.instituciones,name='instituciones'),
    path('instituciones/crear/', usuarios_views.crear_instituciones,name='crear_instituciones'),
    path('instituciones/<int:institucion_id>/', usuarios_views.detalle_instituciones,name='detalle_institucion'),
    path('instituciones/<int:institucion_id>/eliminar/', usuarios_views.eliminar_instituciones,name='eliminar_institucion'),
    path('institucion/editar/<int:id>/', usuarios_views.editar_institucion, name='editar_institucion'),

    # Rol  De Centros De Formacion
    path('centroformacion/', usuarios_views.centrosformacion,name='centrosformacion'),
    path('centroformacion/crear/', usuarios_views.crear_centrosformacion,name='crear_centrosformacion'),
    path('centroformacion/<int:centroformacion_id>/', usuarios_views.detalle_centrosformacion,name='detalle_centrosformacion'),
    path('centroformacion/<int:centroformacion_id>/eliminar/', usuarios_views.eliminar_centrosformacion,name='eliminar_centrosformacion'),


    # ROL Representantes Legales
    path('represantesLegales/', usuarios_views.representante_legal,name='represantesLegales'),
    path('represantesLegales/crear/', usuarios_views.crear_representante_legal,name='crearRepresantesLegales'),
    path('represantesLegales/<int:repreLegal_id>/', usuarios_views.detalle_representante_legal,name='detalleRepresanteLegal'),
    path('represantesLegales/<int:repreLegal_id>/eliminar', usuarios_views.eliminar_representante_legal,name='eliminarRepresanteLegal'),

    # ROL Instructores
    path('gestion_instructor/', gestion_instructores_views.gestion_instructor,name='gestion_instructor'),
    path('get_tree_instructor/', formacion_views.tree_detalle,name='get_tree_instructor'),

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
    path('competencias/crear/', formacion_views.crear_competencias, name='crear_competencias'),

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
    path('pre_matricula/', matricula_views.grupos_prematricula, name='pre_matricula'),
    path('grupo/crear', matricula_views.crear_grupo, name='crear_grupo'),
    path('asignar_aprendices/<int:grupo_id>/', matricula_views.asignar_aprendices, name='asignar_aprendices'),
    path('confirmar_documentacion/<int:grupo_id>/', matricula_views.confirmar_documentacion, name='confirmar_documentacion'),
    path('subir_documento_prematricula/<int:documento_id>/<int:aprendiz_id>/<int:grupo_id>/', matricula_views.cargar_documento_prematricula, name='subir_documento_prematricula'),
    path('pre_matricula/<int:grupo_id>/detalle/', matricula_views.ver_docs_prematricula_grupo, name='ver_docs_prematricula'),
    path('eliminar_documento_pre/<int:documento_id>', matricula_views.eliminar_documento_pre, name='eliminar_documento_pre'),
    path('insti-autocomplete/', matricula_views.InstiAutocomplete.as_view(), name='insti-autocomplete'),
    path('subir_documento_prematricula_insti/<int:documento_id>/<int:institucion_id>/', matricula_views.cargar_documento_institucion, name='cargar_documentos_institucion'),
    path('eliminar_documento_pre_insti/<int:documento_id>/', matricula_views.eliminar_documento_pre_insti, name='eliminar_documento_pre_insti'),
    path('asignar_institucion_gestor/', matricula_views.asignar_institucion_gestor, name='asignar_institucion_gestor'),


    path('cargar_aprendices_masivo/', usuarios_views.cargar_aprendices_masivo, name='cargar_aprendices_masivo'),
    path('descargar_documentos_zip/<int:aprendiz_id>/', matricula_views.descargar_documentos_zip, name='descargar_documentos_zip'),
    path('descargar_documentos_grupo_zip/<int:grupo_id>/', matricula_views.descargar_documentos_grupo_zip, name='descargar_documentos_grupo_zip'),
    path('confirmar_documento/<int:documento_id>/<int:grupo_id>/', matricula_views.confirmar_documento, name='confirmar_documento'),
    path('confirmar_documento_insti/<int:documento_id>/<int:institucion_id>/', matricula_views.confirmar_documento_insti, name='confirmar_documento_insti'),

    path('grupos/<int:grupo_id>/descargar_documentos/<str:documento_tipo>/', matricula_views.descargar_documentos_grupo, name='descargar_documentos_grupo',),
    # Endpoints matricula:
    # API instituciones educativas
    path('api/data/', usuarios_views.T_insti_edu_APIView.as_view(), name='t_insti_edu_api'),
    
    # Endpoint editar instituciones educativas modal
    path('api/institucion/<int:institucion_id>/', usuarios_views.obtener_institucion, name='api_obtener_institucion_modal'),

    # Endpoint editar aprendices modal
    path('api/aprendiz/<int:aprendiz_id>/', usuarios_views.obtener_aprendiz, name='api_obtener_aprendiz_modal'),

    # API llenado de filtros
    path('api/municipios/', matricula_views.obtener_opciones_municipios, name='api_municipios'),
    path('api/estados/', matricula_views.obtener_opciones_estados, name='api_estados'),
    path('api/sectores/', matricula_views.obtener_opciones_sectores, name='api_sectores'),

    # API filtrado de instituciones asignadas

    path('api/filtrar-instituciones/', matricula_views.filtrar_instituciones, name='api_filtrar_instituciones'),
    path('api/institucion_gestor/eliminar/<int:id>/', matricula_views.eliminar_institucion_gestor, name='eliminar_institucion_gestor'),

    # API eliminar grupos
    path('api/grupo/eliminar/<int:id>/', matricula_views.eliminar_grupos, name='eliminar_grupos'),

    
    path('api/grupo/aprendiz/eliminar/<int:id>/', matricula_views.eliminar_relacion_aprendiz_grupos, name='eliminar_relacion_aprendiz_grupos'),

    # path('ruta-a-obtener-municipios/<int:departamento_id>/', formacion_views.get_municipios, name='get_municipios'),
    # path('ruta-a-obtener-instituciones/<int:municipio_id>/', formacion_views.get_instituciones, name='get_instituciones'),
    # path('ruta-a-obtener-centros/<int:departamento_id>/', formacion_views.get_centros, name='get_centros'),
    path('cargar-municipios/', matricula_views.cargar_municipios, name='cargar_municipios'),
    path('cargar-centros/', matricula_views.cargar_centros, name='cargar_centros'),
    path('cargar-instituciones/', matricula_views.cargar_instituciones, name='cargar_instituciones'),

    path('instituciones_gestor/', matricula_views.instituciones_gestor, name='instituciones_gestor'),
    path('instituciones_docs/<int:institucion_id>/', matricula_views.instituciones_docs, name='instituciones_docs'),

    # Ofertas
    path('ofertas/', admin_views.ofertas, name='ofertas'),
    path('ofertas/crear/', admin_views.crear_ofertas, name='crear_ofertas'),
    path('ofertas/show/', admin_views.ofertas_show, name='ofertas_show'),
    path('ofertas/<int:oferta_id>/', admin_views.detalle_oferta, name='ofertas_detalle'),
    path('ofertas/<int:oferta_id>/postular/', admin_views.postular_oferta, name='postular_oferta'),
    path('mis-postulaciones/', admin_views.mis_postulaciones, name='mis_postulaciones'),
    path('ver_postulantes/<int:oferta_id>/', admin_views.ver_postulantes, name='ver_postulantes'),
    path('ver_postulantes_detalle/<int:postulacion_id>', admin_views.ver_postulantes_detalle, name='ver_postulantes_detalle'),

]       

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
