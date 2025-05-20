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

    # API modal perfil de aprendiz
    path('api/aprendices/modal/ver_perfil_aprendiz/<int:aprendiz_id>', usuarios_views.ver_perfil_aprendiz, name='ver_perfil_aprendiz'),

    # Instructores
    
    path('instructores/', usuarios_views.instructores, name='instructores'),
    path('api/instructor/crear/', usuarios_views.crear_instructor,name='crear_instructor'),
    path('api/instructor/<int:instructor_id>/', usuarios_views.obtener_instructor ,name='api_obtener_instructor'),
    path('api/instructor/editar/<int:instructor_id>/', usuarios_views.editar_instructor, name='api_editar_instructor'),
    path('cargar_instructores_masivo/', usuarios_views.cargar_instructores_masivo, name='cargar_instructores_masivo'),

    # Rol Administradores
    path('administradores/', usuarios_views.administradores, name='administradores'),
    path('api/administrador/crear/', usuarios_views.crear_administrador,name='api_crear_administrador'),
    path('api/administrador/<int:admin_id>/', usuarios_views.obtener_administrador ,name='api_obtener_administrador'),
    path('api/administrador/editar/<int:admin_id>/', usuarios_views.editar_administrador, name='api_editar_administrador'),
    path('api/administrador/eliminar/<int:admin_id>/', usuarios_views.eliminar_administrador, name='api_eliminar_administrador'),
    
    # ROL Gestores
    path('gestores/', usuarios_views.gestores, name='gestores'),
    path('api/gestor/crear/', usuarios_views.crear_gestor, name='api_crear_gestor'),
    path('api/gestor/<int:gestor_id>/', usuarios_views.obtener_gestor, name='api_obtener_gestor'), 
    path('api/gestor/editar/<int:gestor_id>/', usuarios_views.editar_gestor, name='api_editar_gestor'), 

    # ROL Cuentas
    path('cuentas/', usuarios_views.cuentas, name='cuentas'),
    path('cuentas/crear/', usuarios_views.crear_pcuentas, name='crear_pcuentas'),
    path('cuentas/<int:cuentas_id>/', usuarios_views.cuentas_detalle, name='cuentas_detalle'),

    # ROL Lideres
    path('lideres/', usuarios_views.lideres, name='lideres'),
    path('api/lider/crear/', usuarios_views.crear_lider, name='api_crear_lideres'),
    path('api/lider/<int:lider_id>/',usuarios_views.obtener_lider, name='api_obtener_lider'),
    path('api/lider/editar/<int:lider_id>/',usuarios_views.editar_lider, name='api_editar_lider'),
    path('api/lider/eliminar/<int:lider_id>/',usuarios_views.eliminar_lider, name='api_eliminar_lider'),

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

    # Endpoint departamento
    path('api/departamentos/', usuarios_views.obtener_departamentos, name='api_departamentos'),

    # ROL Instituciones
    path('instituciones/', usuarios_views.instituciones,name='instituciones'),
    path('instituciones/crear/', usuarios_views.crear_instituciones,name='crear_instituciones'),
    path('instituciones/<int:institucion_id>/eliminar/', usuarios_views.eliminar_instituciones,name='eliminar_institucion'),
    path('api/institucion/editar/<int:institucion_id>/', usuarios_views.editar_institucion, name='api_editar_institucion'),

    path('api/cargar_documentos_multiples_insti/<int:institucion_id>/', matricula_views.cargar_documentos_institucion_multiples, name='cargar_documentos_institucion_multiples'),
    path('api/institucion/rechazar_documento/<int:docu_id>/<int:insti_id>/', matricula_views.rechazar_documento_insti, name='rechazar_documento_insti'),
    path('api/institucion/obtener-historial/<int:institucion_id>/', matricula_views.obtener_historial_institucion, name='obtener_historial_institucion'),

    # Rol Centros De Formacion
    path('centroformacion/', usuarios_views.centrosformacion,name='centrosformacion'),
    path('api/centro/crear/', usuarios_views.crear_centro,name='api_crear_centro'),

    # Endpoint listar centros de formacion
    path('api/centro/', usuarios_views.listar_centros_formacion_json, name='api_listar_centro'),

    # Endpoint editar centros modal
    path('api/centro/<int:centro_id>/', usuarios_views.obtener_centro, name='api_obtener_centro_modal'),
    path('api/centro/editar/<int:centro_id>/', usuarios_views.editar_centro, name='api_editar_centro'),

    # Endpoint eliminar centro
    path('api/centro/eliminar/<int:centro_id>/', usuarios_views.eliminar_centro, name='api_eliminar_centro'),

    # ROL Instructores
    path('gestion_instructor/', gestion_instructores_views.gestion_instructor,name='gestion_instructor'),

    # Panel instructor
    path('fichas_inst/', formacion_views.listar_fichas, name='listar_fichas'),

    # Tree
    path("api/tree/obtener_carpetas/<int:ficha_id>/", formacion_views.obtener_carpetas, name="api_obtener_carpetas"),
    path("api/tree/cargar_doc/", formacion_views.cargar_documento, name="api_cargar_documento"),
    path('api/tree/eliminar_documento/<int:documento_id>', formacion_views.eliminar_documento_portafolio_ficha, name='api_eliminar_documento_portafolio_ficha'),
    path('api/tree/obtener_hijos_carpeta/<int:carpeta_id>', formacion_views.obtener_hijos_carpeta, name='api_obtener_hijos_carpeta'),

    # Tree aprendiz
    path("api/tree/obtener_carpetas_aprendiz/<int:aprendiz_id>/", formacion_views.obtener_carpetas_aprendiz, name="api_obtener_carpetas_aprendiz"),
    path("api/tree/cargar_doc_aprendiz/", formacion_views.cargar_documento_aprendiz, name="api_cargar_documento_aprendiz"),
    path('api/tree/eliminar_documento_aprendiz/<int:documento_id>', formacion_views.eliminar_documento_portafolio_aprendiz, name='api_eliminar_documento_portafolio_aprendiz'),
    path('api/tree/obtener_hijos_carpeta_aprendiz/<int:carpeta_id>', formacion_views.obtener_hijos_carpeta_aprendiz, name='api_obtener_hijos_carpeta_aprendiz'),

    #Fichas
    path('ficha/<int:ficha_id>/', formacion_views.panel_ficha, name='panel_ficha'),
    path('api/ficha/crear_actividad/<int:ficha_id>/', formacion_views.crear_actividad, name='api_crear_actividad'),
    path('api/ficha/calificar_actividad/', formacion_views.calificarActividad, name='api_calificar_actividad_ficha'),
    path('api/ficha/ver_cronograma/<int:ficha_id>/', formacion_views.listar_actividades_ficha, name='api_listar_actividades_ficha'),
    path('api/ficha/obtener_aprendices_calificacion/<int:ficha_id>/<int:actividad_id>/', formacion_views.obtener_aprendices_calificacion, name='api_obtener_aprendices_calificacion'),
    path('api/ficha/detalle_actividad/<int:actividad_id>', formacion_views.detalle_actividad, name='api_detalle_actividad'),
    path('api/ficha/encuentro_detalle/<int:encuentro_id>/', formacion_views.detalle_encuentro, name='api_detalle_encuentro'),
    path('api/ficha/cerrar_fase/<int:ficha_id>/', formacion_views.cerrar_fase_ficha, name='api_cerrar_fase_ficha'),
    path('api/ficha/devolver_fase/<int:ficha_id>/', formacion_views.devolver_fase_ficha, name='api_devolver_fase_ficha'),
    path('api/ficha/actividad/<int:actividad_id>/', formacion_views.obtener_actividad, name='api_obtener_actividad'),
    path('api/ficha/actividad/editar/<int:actividad_id>/', formacion_views.editar_actividad, name='api_editar_actividad'),
    path('api/ficha/actividades/<int:ficha_id>/', formacion_views.obtener_actividades, name='api_obtener_actividades'),
    path('api/ficha/obtener_estado_fase/<int:ficha_id>/', formacion_views.obtener_estado_fase, name='api_obtener_estado_fase'),
    path('api/ficha/crear_encuentro/<int:ficha_id>/', formacion_views.crear_encuentro, name='api_crear_encuentro'),
    path('api/ficha/encuentros/<int:ficha_id>/', formacion_views.obtener_encuentros, name='api_obtener_encuentros'),

    # Reportes ficha
    path('api/reporte/ficha/generar_acta_asistencia/', formacion_views.generar_acta_asistencia, name='generar_acta_asistencia'),
    path('api/reporte/ficha/generar_acta_asistencia_aprendiz/', formacion_views.generar_acta_asistencia_aprendiz, name='generar_acta_asistencia_aprendiz'),
    path('api/reporte/ficha/generar_informe_calificaciones/', formacion_views.generar_informe_calificaciones, name='generar_informe_calificaciones'),

    # ROL Aprendices
    path('panel_aprendiz/', formacion_views.panel_aprendiz, name='panel_aprendiz'),

    # Novedades
    path('novedades/', usuarios_views.novedades, name='novedades'),
    path('novedades/crear/', usuarios_views.crear_novedad , name='crear_novedad'),

    # Fichas
    path('fichas/', formacion_views.fichas, name='fichas'), 
    path('api/formalizar_ficha/', matricula_views.formalizar_ficha, name='api_formalizar_ficha'), 

    # Programas
    path('programas/', formacion_views.listar_programas, name='programas'),
    path('programas/crear/', formacion_views.crear_programa, name='crear_programas'),
    path('api/programa/detalle/<int:programa_id>/', formacion_views.detalle_programa, name='api_detalle_programa'),

    # Competencias
    path('competencias/', formacion_views.competencias, name='competencias'),
    path('api/competencia/crear/', formacion_views.crear_competencia, name="api_crear_competencia"),
    path('api/competencias/filtrar/', formacion_views.filtrar_competencias, name="api_filtrar_competencias"),
    path('api/competencias/fases/', formacion_views.obtener_opciones_fases, name="api_opciones_fases"),
    path('api/competencias/programas/', formacion_views.obtener_opciones_programas, name="api_opciones_programas"),
    path('api/competencia/<int:competencia_id>/', formacion_views.obtener_competencia, name="api_obtener_competencia"),
    path('api/competencia/editar/<int:competencia_id>/', formacion_views.editar_competencia, name="api_editar_competencia"),

    # RAPS
    path('raps/', formacion_views.listar_raps, name = 'raps'),
    path('api/rap/crear/', formacion_views.crear_rap, name = 'api_crear_rap'),
    path('api/raps/filtrar/', formacion_views.filtrar_raps, name="api_filtrar_raps"),
    path('api/raps/fases/', formacion_views.obtener_opciones_fases_raps, name="api_opciones_fases_raps"),
    path('api/raps/programas/', formacion_views.obtener_opciones_programas_raps, name="api_opciones_programas_raps"),
    path('api/raps/competencias/', formacion_views.obtener_opciones_competencias_raps, name="api_opciones_competencias_raps"),
    path('api/rap/<int:rap_id>/', formacion_views.obtener_rap, name="api_obtener_rap"),

    path('api/competencias/', formacion_views.obtener_opciones_competencias, name="api_opciones_competencias"),
    path('api/rap/editar/<int:rap_id>/', formacion_views.editar_rap, name="api_editar_rap"),


    path('api/competencias_progra/<int:id_progra>/', formacion_views.obtener_competencias_programa, name = 'api_obtener_competencias_programa'),
    

    # Guias
    path('guias/', formacion_views.listar_guias, name = 'guias'),
    path('api/guia/crear/', formacion_views.crear_guia, name='api_crear_guia'),
    path('api/guia/<int:guia_id>/', formacion_views.obtener_guia, name='api_obtener_guia'),
    path('api/guia/editar/<int:guia_id>/', formacion_views.editar_guia, name='api_editar_guia'),

    # Tree
    path('api/carpetas/<int:ficha_id>/', formacion_views.obtener_carpetas, name='obtener_carpetas'),
    path('api/estudiantes/<int:ficha_id>/', formacion_views.listar_estudiantes, name='listar_estudiantes'),

    # Eliminar documentos
    path('eliminar_documento/<int:documento_id>/', formacion_views.eliminar_doc, name='eliminar_documento'),

    # Pre matricula
    path('pre_matricula/', matricula_views.grupos_prematricula, name='pre_matricula'),
    path('grupo/crear', matricula_views.crear_grupo, name='crear_grupo'),
    path('asignar_aprendices/<int:grupo_id>/', matricula_views.asignar_aprendices, name='asignar_aprendices'),
    path('confirmar_documentacion/<int:grupo_id>/', matricula_views.confirmar_documentacion, name='confirmar_documentacion'),
    path('pre_matricula/<int:grupo_id>/detalle/', matricula_views.ver_docs_prematricula_grupo, name='ver_docs_prematricula'),
    path('insti-autocomplete/', matricula_views.InstiAutocomplete.as_view(), name='insti-autocomplete'),
    path('subir_documento_prematricula_insti/<int:documento_id>/<int:institucion_id>/', matricula_views.cargar_documento_institucion, name='cargar_documentos_institucion'),
    path('eliminar_documento_pre_insti/<int:documento_id>/', matricula_views.eliminar_documento_pre_insti, name='eliminar_documento_pre_insti'),
    path('asignar_institucion_gestor/', matricula_views.asignar_institucion_gestor, name='asignar_institucion_gestor'),
    path('api/prematricula/documentos_aprendiz/<int:aprendiz_id>/', matricula_views.obtener_documentos_prematricula, name='obtener_documentos_prematricula'),
    path('api/prematricula/historial_doc_aprendiz/<int:aprendiz_id>/', matricula_views.obtener_historial_prematricula, name='obtener_historial_prematricula'),
    path('api/prematricula/subir_documento/<int:documento_id>/', matricula_views.cargar_documento_prematricula, name='cargar_documento_prematricula'),
    path('api/prematricula/eliminar_documento/<int:documento_id>', matricula_views.eliminar_documento_prematricula, name='eliminar_documento_prematricula'),
    path('api/prematricula/aprobar_documento/<int:doc_id>/', matricula_views.aprobar_documento_prematricula, name="aprobar_documento_prematricula"),
    path('api/prematricula/rechazar_documento/<int:doc_id>/', matricula_views.rechazar_documento_prematricula, name="rechazar_documento_prematricula"),


    path('cargar_aprendices_masivo/', usuarios_views.cargar_aprendices_masivo, name='cargar_aprendices_masivo'),
    path('descargar_documentos_zip/<int:aprendiz_id>/', matricula_views.descargar_documentos_zip, name='descargar_documentos_zip'),
    path('descargar_documentos_grupo_zip/<int:grupo_id>/', matricula_views.descargar_documentos_grupo_zip, name='descargar_documentos_grupo_zip'),
    path('confirmar_documento/<int:documento_id>/<int:grupo_id>/', matricula_views.confirmar_documento, name='confirmar_documento'),
    path('confirmar_documento_insti/<int:documento_id>/<int:institucion_id>/', matricula_views.confirmar_documento_insti, name='confirmar_documento_insti'),

    path('grupos/<int:grupo_id>/descargar_documentos/<str:documento_tipo>/', matricula_views.descargar_documentos_grupo, name='descargar_documentos_grupo',),
    # Endpoints matricula:
    # API instituciones educativas
    path('api/institucion/', usuarios_views.listar_instituciones, name='t_insti_edu_api'),
    
    # EndPoint filtros institucion
    path('api/institucion/departamento/', usuarios_views.obtener_departamentos_filtro_insti, name='obtener_departamentos_filtro_insti'),
    path('api/institucion/municipio/', usuarios_views.obtener_municipio_filtro_insti, name='obtener_municipio_filtro_insti'),
    path('api/institucion/estado/', usuarios_views.obtener_estado_filtro_insti, name='obtener_estado_filtro_insti'),
    path('api/institucion/zona/', usuarios_views.obtener_zona_filtro_insti, name='obtener_zona_filtro_insti'),

    # Endpoint editar instituciones educativas modal
    path('api/institucion/<int:institucion_id>/', usuarios_views.obtener_institucion, name='api_obtener_institucion_modal'),

    # Endpoint ver institucion modal
    path('api/institucion/modal/ver_institucion/<int:institucion_id>/', usuarios_views.obtener_institucion_modal, name='obtener_institucion_modal'),


    # Endpoint editar aprendices modal
    path('api/aprendiz/<int:aprendiz_id>/', usuarios_views.obtener_aprendiz, name='api_obtener_aprendiz_modal'),

    # API llenado de filtros
    path('api/municipios/', matricula_views.obtener_opciones_municipios, name='api_municipios'),
    path('api/estados/', matricula_views.obtener_opciones_estados, name='api_estados'),
    path('api/sectores/', matricula_views.obtener_opciones_sectores, name='api_sectores'),

    path('api/listar_municipios/', usuarios_views.api_municipios, name='api_municipios'),


    # API filtrado de instituciones asignadas

    path('api/institucion/filtrar_instituciones_gestor/', matricula_views.filtrar_instituciones_gestor, name='api_filtrar_instituciones_gestor'),
    path('api/institucion_gestor/eliminar/<int:id>/', matricula_views.eliminar_institucion_gestor, name='eliminar_institucion_gestor'),

    # API eliminar grupos
    path('api/grupo/eliminar/<int:id>/', matricula_views.eliminar_grupos, name='eliminar_grupos'),

    path('dividir_pdf/', matricula_views.dividir_pdf, name='dividir_pdf'),

    
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

    path('rechazar_perfil/<int:postulacion_id>/', admin_views.rechazar_perfil, name='rechazar_perfil'),
    path('desistir_postulacion/<int:postulacion_id>/', admin_views.desistir_postulacion, name='desistir_postulacion'),

    # Contratos
    path('contratos/', admin_views.contratos, name='contratos'),

    path('reset-password/', usuarios_views.reset_password_view, name='reset_password'),

    # Gestion de usuarios
    path('usuarios/', usuarios_views.usuarios, name='usuarios'),
    path('api/usuario/restablecer_contrasena/', usuarios_views.restablecer_contrasena, name='api_restablecer_contrasena'),

]  

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
