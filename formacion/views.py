from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from .forms import CascadaMunicipioInstitucionForm, CargarDocuPortafolioFichaForm, ActividadForm,RapsFichaForm, EncuApreForm, EncuentroForm, DocumentosForm, CronogramaForm, ProgramaForm, CompetenciaForm, RapsForm, FichaForm
from commons.models import T_centro_forma, T_prematri_docu ,T_docu, T_munici, T_insti_edu, T_acti_apre,T_raps_acti,T_perfil, T_DocumentFolderAprendiz, T_encu_apre, T_apre, T_raps_ficha, T_acti_ficha, T_ficha, T_crono, T_progra, T_fase_ficha ,T_instru, T_acti_docu, T_perfil, T_compe, T_raps, T_DocumentFolder
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required
from datetime import datetime
from .scripts.cargar_tree import crear_datos_prueba 
from .scripts.cargar_tree_apre import crear_datos_prueba_aprendiz
from django.conf import settings
from django.core.files.storage import default_storage
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib import messages

# Create your views here.

def crear_ficha(request):
    if request.method == 'POST':
        ficha_form = FichaForm(request.POST)
        cascadaform = CascadaMunicipioInstitucionForm(request.POST)

        if ficha_form.is_valid() and cascadaform.is_valid():
            try:
                centro = cascadaform.cleaned_data.get('centro')
                institucion = cascadaform.cleaned_data.get('insti')
                print("Paso 2")
                print(centro)
                print(institucion)

                # # Crear la ficha
                # new_ficha = ficha_form.save(commit=False)
                # new_ficha.esta = "prematricula"
                # new_ficha.num_apre_pendi_regi = new_ficha.num_apre_proce
                # new_ficha.num_apre_forma = "0"
                
                # ficha = ficha_form.save()

                # # Crear las fases asociadas a la ficha
                # fases = ['Analisis', 'Planeacion', 'Ejecucion', 'Evaluacion']
                # for fase in fases:
                #     if fase == 'Analisis':
                #         fecha_inia = ficha.fecha_aper
                #         vige1 = 'Si'
                #     else:
                #         fecha_inia = None
                #         vige1 = 'No'
                #     T_fase_ficha.objects.create(
                #         fase=fase,
                #         ficha=ficha,
                #         fecha_ini=fecha_inia,
                #         instru=ficha.instru,
                #         vige=vige1
                #     )

                # # Crear competencias y raps asociadas a la ficha
                # programa = ficha.progra
                # competencias = T_compe.objects.filter(progra=programa)
                # raps = T_raps.objects.filter(compe__in=competencias)
                # for rap in raps:
                #     T_raps_ficha.objects.create(ficha=ficha, rap=rap)

                # # Llamar a la función para crear estructura de carpetas asociada a la ficha
                # crear_datos_prueba(ficha.id)

                # # Redirigir con un mensaje de éxito
                # messages.success(request, 'Ficha creada exitosamente.')
                return redirect('fichas_adm')
            except Exception as e:
                messages.error(request, f'Ocurrió un error al crear la ficha: {str(e)}')
        else:
            # Mostrar errores específicos del formulario en los mensajes
            errores = ficha_form.errors.as_data()
            for campo, errores_campo in errores.items():
                for error in errores_campo:
                    mensaje_error = error.message
                    messages.error(request, f"Error en el campo '{campo}': {mensaje_error}")
    else:
        ficha_form = FichaForm()
        cascadaform = CascadaMunicipioInstitucionForm()
    return render(request, 'crear_ficha.html', {
        'ficha_form': ficha_form,
        'cascadaform': cascadaform
    })



def listar_fichas_adm(request):
    fichas = T_ficha.objects.all()
    return render(request, 'listar_fichas.html', {'fichas': fichas})

@login_required
def listar_fichas(request):
    perfil = getattr(request.user, 't_perfil', None)
    if perfil is None or perfil.rol != 'instructor':
        return render(request, 'fichas.html', {'mensaje': 'No tienes permisos para acceder a esta página.'})
    
    instructor = T_instru.objects.filter(perfil=perfil).first()

    if not instructor:
        return render(request, 'fichas.html', {'mensaje': 'No se encontraron fichas asociadas a este instructor.'})

    fichas = T_ficha.objects.filter(instru=instructor)
    
    print(fichas)
    return render(request, 'fichas.html', {'fichas': fichas})

@login_required
def panel_ficha(request, ficha_id):
    ficha = get_object_or_404(T_ficha, id=ficha_id)
    actividades = T_acti_ficha.objects.filter(ficha=ficha)
    fase = T_fase_ficha.objects.filter(ficha_id=ficha_id, vige='Si').first()
    print(fase)
    raps_count = T_raps_ficha.objects.filter(ficha=ficha_id, agre='No').count()
    aprendices = T_apre.objects.filter(ficha=ficha_id)
    encuentros = T_encu_apre.objects.filter(ficha=ficha.id)
    if request.method == 'POST':
        encuentro_form = EncuentroForm(request.POST)
        if encuentro_form.is_valid():
            encuentro_form.save()
            return redirect('panel_ficha', ficha_id=ficha.id)
    else:
        encuentro_form = EncuentroForm()

    
    return render(request, 'panel_instructor.html', {
        'ficha': ficha,
        'actividades': actividades,
        'fase': fase,
        'raps_count': raps_count,
        'aprendices': aprendices,
        'encuentro_form': encuentro_form,
        'encuentros': encuentros
    })

@login_required
def prueba_tree(request):
    return render(request, 'prueba_tree.html')

def obtener_carpetas(request, ficha_id):
    # Obtener las carpetas raíz asociadas a la ficha
    carpetas = T_DocumentFolder.objects.filter(parent__isnull=True, ficha = ficha_id)

    # Función recursiva para obtener subcarpetas y documentos
    def obtener_subcarpetas(carpeta):
        subcarpetas = []
        for subcarpeta in carpeta.get_children():
            subcarpeta_data = {
                "title": subcarpeta.name,
                "id": subcarpeta.id,  # Incluye un id único
                "type": subcarpeta.tipo,  # Extrae el tipo directamente
                "children": obtener_subcarpetas(subcarpeta) if subcarpeta.tipo == "carpeta" else []  # Solo carpetas tendrán hijos
            }
            if subcarpeta.tipo == "documento":
                if subcarpeta.url:  # Comprobar que el campo url no sea None
                    subcarpeta_data["url"] = settings.MEDIA_URL + subcarpeta.url  # Esto genera la URL correcta del archivo
                else:
                    subcarpeta_data["url"] = None  # Si no hay archivo, dejar URL como None
            else:
                subcarpeta_data["url"] = subcarpeta.url
            subcarpetas.append(subcarpeta_data)
        return subcarpetas
    
    # Construir los datos para la respuesta JSON
    data = []
    for carpeta in carpetas:
        carpeta_data = {
            "title": carpeta.name,
            "id": carpeta.id,  # Incluye un id único
            "url": carpeta.url,  # Coloca el url directamente
            "type": carpeta.tipo,  # Extrae el tipo directamente
            "children": obtener_subcarpetas(carpeta)  # Llamada recursiva para subcarpetas
        }
        
        data.append(carpeta_data)

    return JsonResponse(data, safe=False)

def obtener_carpetas_aprendiz(request, ficha_id, aprendiz_id):
    # Obtener las carpetas raíz asociadas a la ficha
    carpetas = T_DocumentFolderAprendiz.objects.filter(parent__isnull=True, ficha = ficha_id, aprendiz = aprendiz_id)

    # Función recursiva para obtener subcarpetas y documentos
    def obtener_subcarpetas(carpeta):
        subcarpetas = []
        for subcarpeta in carpeta.get_children():
            subcarpeta_data = {
                "title": subcarpeta.name,
                "id": subcarpeta.id,  # Incluye un id único
                "type": subcarpeta.tipo,  # Extrae el tipo directamente
                "children": obtener_subcarpetas(subcarpeta) if subcarpeta.tipo == "carpeta" else []  # Solo carpetas tendrán hijos
            }
            if subcarpeta.tipo == "documento":
                if subcarpeta.url:  # Comprobar que el campo url no sea None
                    subcarpeta_data["url"] = settings.MEDIA_URL + subcarpeta.url  # Esto genera la URL correcta del archivo
                else:
                    subcarpeta_data["url"] = None  # Si no hay archivo, dejar URL como None
            else:
                subcarpeta_data["url"] = subcarpeta.url
            subcarpetas.append(subcarpeta_data)
        return subcarpetas
    
    # Construir los datos para la respuesta JSON
    data = []
    for carpeta in carpetas:
        carpeta_data = {
            "title": carpeta.name,
            "id": carpeta.id,  # Incluye un id único
            "url": carpeta.url,  # Coloca el url directamente
            "type": carpeta.tipo,  # Extrae el tipo directamente
            "children": obtener_subcarpetas(carpeta)  # Llamada recursiva para subcarpetas
        }
        
        data.append(carpeta_data)

    return JsonResponse(data, safe=False)

def crear_encuentro(request, ficha_id):
    ficha = get_object_or_404(T_ficha, id=ficha_id)  # Obtener la ficha seleccionada
    if request.method == 'POST':
        encuentro_form = EncuentroForm(request.POST)
        encuapre_form = EncuApreForm(request.POST, ficha=ficha)
        if encuentro_form.is_valid() and encuapre_form.is_valid():

            new_encuentro = encuentro_form.save(commit=False)
            new_encuentro.ficha = ficha
            new_encuentro.save()
            aprendices_seleccionados = encuapre_form.cleaned_data['aprendices']
            aprendices_ficha = T_apre.objects.filter(ficha=ficha)
            aprendices_seleccionados_set = set(aprendices_seleccionados)

            # Iteramos sobre los estudiantes de la ficha
            for aprendiz in aprendices_ficha:
                # Verificamos si el estudiante está en los seleccionados
                if aprendiz in aprendices_seleccionados_set:
                    # Si está en los seleccionados, aseguramos que el campo 'prese' sea 'Si'
                    T_encu_apre.objects.update_or_create(
                        encu=new_encuentro,  
                        apre=aprendiz,
                        ficha = ficha,
                        defaults={'prese': 'No'}
                    )
                else:
                    # Si no está en los seleccionados, aseguramos que el campo 'prese' sea 'No'
                    T_encu_apre.objects.update_or_create(
                        encu=new_encuentro,  
                        apre=aprendiz,
                        ficha = ficha,
                        defaults={'prese': 'Si'}
                    )

            # Ahora creamos los registros para los estudiantes seleccionados
            for aprendiz_encu in aprendices_seleccionados:
                # Verificamos si el estudiante ya existe en la tabla T_encu_apre
                T_encu_apre.objects.update_or_create(
                    encu=new_encuentro,
                    apre=aprendiz_encu,
                    ficha = ficha,
                    defaults={'prese': 'No'}
                )

            return redirect('panel_ficha', ficha_id=ficha.id)
    else:
        # Pasa 'ficha' al formulario en GET también
        encuentro_form = EncuentroForm()
        encuapre_form = EncuApreForm(ficha=ficha)
    return render(request, 'crear_encuentro.html', {
        'encuentro_form': encuentro_form, 
        'encuapre_form': encuapre_form,
        'ficha': ficha
        })

@login_required
def crear_actividad(request, ficha_id):
    ficha = get_object_or_404(T_ficha, id=ficha_id)

    if request.method == 'GET':
        actividad_form = ActividadForm()
        documento_form = DocumentosForm()
        cronograma_form = CronogramaForm()
        raps_form = RapsFichaForm(ficha=ficha)


        return render(request, 'actividad_crear.html', {
            'ficha': ficha,
            'actividad_form': actividad_form,
            'documento_form': documento_form,
            'cronograma_form': cronograma_form,
            'raps_form': raps_form
        })
    else:
        actividad_form = ActividadForm(request.POST)
        documento_form = DocumentosForm(request.POST, request.FILES)
        cronograma_form = CronogramaForm(request.POST)
        raps_form = RapsFichaForm(request.POST, ficha=ficha)

        if not all([
            actividad_form.is_valid(),
            documento_form.is_valid(),
            cronograma_form.is_valid(),
            raps_form.is_valid()
        ]):
            # Si algún formulario no es válido, devolvemos los formularios con los errores
            return render(request, 'actividad_crear.html', {
                'actividad_form': actividad_form,
                'documento_form': documento_form,
                'cronograma_form': cronograma_form,
                'raps_form': raps_form,
                'error': 'Por favor, corrige los errores en los formularios.'
            })

        try:
            # Obtener el instructor logueado
            perfil = getattr(request.user, 't_perfil', None)
            instructor = T_instru.objects.get(perfil=perfil)

            # Creación de la actividad
            fase = T_fase_ficha.objects.filter(ficha_id=ficha_id, vige='Si').first()
            new_actividad = actividad_form.save(commit=False)
            new_actividad.fase = fase.fase
            new_actividad.save()
            actividad_form.save_m2m()

            # Creación del documento
            archivo = documento_form.cleaned_data['archi']
            nom = archivo.name
            tipo = archivo.name.split('.')[-1]
            tama = str(archivo.size // 1024) + " KB"
            new_documento = documento_form.save(commit=False)
            new_documento.nom = nom
            new_documento.tipo = tipo
            new_documento.tama = tama
            new_documento.priva = 'No'
            new_documento.esta = 'Activo'
            new_documento.save()

            # Asignar la actividad al documento
            T_acti_docu.objects.create(docu=new_documento, acti=new_actividad)

            # Creación del cronograma
            new_cronograma = cronograma_form.save()

            # Crear la actividad en T_acti_ficha
            new_acti_ficha = T_acti_ficha.objects.create(
                ficha=ficha,
                acti=new_actividad,
                crono=new_cronograma,  # Si el formulario incluye cronograma
                esta='Activo'
            )

            # Obtener la lista de aprendices asociados a la ficha
            aprendices = T_apre.objects.filter(ficha=ficha)

            # Crear registros en T_acti_apre
            for aprendiz in aprendices:
                T_acti_apre.objects.create(
                    apre=aprendiz,
                    acti=new_acti_ficha,
                    apro='Pendiente',  # Estado inicial
                    fecha=now()  # Fecha de asignación
                )

            raps_seleccionados = raps_form.cleaned_data['raps']
            print(raps_seleccionados)

             # Crear los registros de raps seleccionados en T_raps_acti
            raps_seleccionados = raps_form.cleaned_data['raps']
            for rap_ficha in raps_seleccionados:
                T_raps_acti.objects.create(
                    rap=rap_ficha.rap,  # RAP seleccionado
                    acti=new_actividad  # Actividad recién creada
                )
                rap_ficha.agre = 'Si'  # Marcar como asignado
                rap_ficha.save()

            return redirect('panel_ficha', ficha_id=ficha.id)

        except ValueError as e:
            return render(request, 'actividad_crear.html', {
                'actividad_form': actividad_form,
                'documento_form': documento_form,
                'cronograma_form': cronograma_form,
                'raps_form': raps_form,
                'error': f'Ocurrió un error: {str(e)}'
            })

    #se debe crear la actividad aprendiz aca
    # se debe crear 

@login_required
def panel_aprendiz(request):
    # Obtener el perfil del usuario logueado
    perfil = T_perfil.objects.filter(user=request.user).first()
    
    # Verificar que el perfil existe
    if perfil:
        # Buscar el aprendiz asociado con ese perfil
        aprendiz = T_apre.objects.filter(perfil=perfil).first()

        # Verificar si el aprendiz tiene ficha asignada
        ficha = aprendiz.ficha if aprendiz else None

        # Obtener el listado de documentos del aprendiz
        documentos = T_prematri_docu.objects.filter(apren=aprendiz) if aprendiz else []

        total_documentos = 0
        for documento in documentos:
            if  documento.esta == "Cargado":
                total_documentos += 1
    else:
        ficha = None
        documentos = []
        total_documentos = 0
    return render(request, 'panel_aprendiz.html', {'ficha': ficha, 'documentos': documentos, 'total_documentos': total_documentos})

@login_required
def tree_detalle(request):
    data = [
    {
        "title": "PLAN DE TRABAJO CONCERTADO CON SUS DESCRIPTORES",
        "id": "1",
        "children": [
            {"title": "Fase Analisis", "id": "1"},
            {"title": "Fase Planeacion", "id": "2"},
            {"title": "Fase Ejecucion", "id": "3"},
            {"title": "Fase Evaluacion", "id": "4"}
        ]
    },
    {
        "title": "GFPI F 135 GUIA DE APRENDIZAJE",
        "id": "2",
        "children": [
            {
                "title": "Fase Analisis",
                "id": "1",
                "children": [
                    {"title": "Guia de la fase", "id": "1"},
                    {"title": "Instrumentos de evaluacion", "id": "2"}
                ]
            },
            {"title": "Fase Planeacion", "id": "2"},
            {"title": "Fase Ejecucion", "id": "3"},
            {"title": "Fase Evaluacion", "id": "4"}
        ]
    }
    ]
    return JsonResponse(data, safe=False)

# Vistas programa

def listar_programas(request):
    programas = T_progra.objects.all()
    return render(request, 'programas.html', {'programas': programas})

def crear_programa(request):
    if request.method == 'POST':
        programa_form = ProgramaForm(request.POST)
        if programa_form.is_valid():
            programa_form.save()
            return redirect('programas')
    else:
        programa_form = ProgramaForm()
    return render(request, 'crear_programa.html', {'programa_form': programa_form})

# Vistas competencia

def listar_competencias(request):
    competencias = T_compe.objects.all()
    return render(request, 'competencias.html', {'competencias': competencias})

def crear_competencias(request):
    if request.method == 'POST':
        competencia_form = CompetenciaForm(request.POST)
        if competencia_form.is_valid():
            competencia_form.save()
            return redirect('competencias')
    else:
        competencia_form = CompetenciaForm()
    return render(request, 'crear_competencia.html', {'competencia_form': competencia_form})

#Vistas Raps
def listar_raps(request):
    raps = T_raps.objects.all()
    return render(request, 'raps.html', {'raps': raps})

def crear_raps(request):
    if request.method == 'POST':
        raps_form = RapsForm(request.POST)
        if raps_form.is_valid():
            raps_form.save()
            return redirect('raps')
    else:
        raps_form = RapsForm()
    return  render(request, 'crear_raps.html', {'raps_form': raps_form})

def cargar_documento(request, ficha_id):
    if request.method == 'POST':
        nuevo_doc_form = CargarDocuPortafolioFichaForm(request.POST)
        carpeta_destino = T_DocumentFolder.objects.get(id=2)
        print(carpeta_destino)
        if nuevo_doc_form.is_valid():
            nombre_documento = nuevo_doc_form.cleaned_data['nombre_documento']
            url_documento = nuevo_doc_form.cleaned_data['url_documento']
            carpeta = nuevo_doc_form.cleaned_data['carpeta']
            print(nombre_documento, url_documento, carpeta)

            # # Crear un nuevo T_DocumentContent (documento) asociado a la carpeta

            nuevo_documento = T_DocumentFolder(
                name=nombre_documento,
                url=url_documento,
                parent=carpeta_destino,  # Aquí asignas el T_DocumentFolder seleccionado como parent de T_DocumentContent
                ficha_id=ficha_id  # Asegúrate de tener el ficha_id en la sesión o el contexto
            )
            nuevo_documento.save()

    else:
        nuevo_doc_form = CargarDocuPortafolioFichaForm()

    return render(request, 'cargar_documento.html', {'form': nuevo_doc_form})

def cargar_link_folders(request, ficha_id, carpeta):
    if request.method == 'POST':
        documento_form = DocumentosForm(request.POST, request.FILES)

        carpeta_destino = T_DocumentFolder.objects.get(iden=carpeta, ficha = ficha_id)
        if documento_form.is_valid():

            # Creación del documento
            archivo = documento_form.cleaned_data['archi']
            nom = archivo.name
            tipo = archivo.name.split('.')[-1]
            tama = str(archivo.size // 1024) + " KB"
            new_documento = documento_form.save(commit=False)
            new_documento.nom = nom
            new_documento.tipo = tipo
            new_documento.tama = tama
            new_documento.priva = 'No'
            new_documento.esta = 'Activo'
            new_documento.save()

            # Crear un nuevo T_DocumentContent (documento) asociado a la carpeta
            new_documento.nom = new_documento.nom.replace(" ", "_")
            nuevo_documento = T_DocumentFolder(
                name=new_documento.nom,
                tipo="documento",
                url="documentos/"+new_documento.nom,
                parent=carpeta_destino,  # Aquí asignas el T_DocumentFolder seleccionado como parent de T_DocumentContent
                ficha_id=ficha_id  # Asegúrate de tener el ficha_id en la sesión o el contexto
            )
            nuevo_documento.save()
            return redirect('panel_ficha', ficha_id=ficha_id)

    else:
        nuevo_doc_form = CargarDocuPortafolioFichaForm()
        documento_form = DocumentosForm()
        carpeta_destino = T_DocumentFolder.objects.get(iden=carpeta, ficha = ficha_id)
        id_carpeta_destino = carpeta_destino.iden


    return render(request, 'cargar_link_folders.html', {
        'form': nuevo_doc_form,
        'documento_form': documento_form,
        'carpeta': id_carpeta_destino
        })

def eliminar_doc(request, documento_id):
    if request.method == "DELETE":
        try:
            documento = T_DocumentFolder.objects.get(id = documento_id)
            documento.delete()
            return JsonResponse({"success": True, "message": "Documento eliminado exitosamente."}, status=200)
        except T_DocumentFolder.DoesNotExist:
            return JsonResponse({"success": False, "message": "Documento no encontrado."}, status=404)
    return JsonResponse({"success": False, "message": "Método no permitido."}, status=405)

def listar_estudiantes(request, ficha_id):
    estudiantes = T_apre.objects.filter(ficha_id=ficha_id)
    data = [
        {
            "id": estudiante.id,
            "nombre": estudiante.perfil.nom,
            "apellido": estudiante.perfil.apelli,
        }
        for estudiante in estudiantes
    ]
    return JsonResponse(data, safe=False)

# Vista para cargar los municipios según el departamento
def get_municipios(request, departamento_id):
    municipio_qs = T_munici.objects.filter(nom_departa_id=departamento_id)
    municipios = list(municipio_qs.values('id', 'nom_munici'))
    return JsonResponse(municipios, safe=False)

# Vista para cargar las instituciones según el municipio
def get_instituciones(request, municipio_id):
    instituciones_qs = T_insti_edu.objects.filter(muni_id=municipio_id)
    instituciones = list(instituciones_qs.values('id', 'nom'))
    return JsonResponse(instituciones, safe=False)

# Vista para cargar los municipios según el departamento
def get_centros(request, departamento_id):
    centro_qs = T_centro_forma.objects.filter(depa_id=departamento_id)
    centros = list(centro_qs.values('id', 'nom'))
    return JsonResponse(centros, safe=False)
