from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.staticfiles import finders
import openpyxl
import logging
from django.http import FileResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from django.utils import timezone 
from django.db.models import Subquery, OuterRef
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from .forms import CascadaMunicipioInstitucionForm,GuiaForm, CargarDocuPortafolioFichaForm, ActividadForm,RapsFichaForm, EncuApreForm, EncuentroForm, DocumentosForm, CronogramaForm, ProgramaForm, CompetenciaForm, RapsForm, FichaForm
from commons.models import T_encu, T_centro_forma,T_guia, T_cali, T_prematri_docu ,T_docu, T_munici, T_insti_edu, T_acti_apre,T_raps_acti,T_perfil, T_DocumentFolderAprendiz, T_encu_apre, T_apre, T_raps_ficha, T_acti_ficha, T_ficha, T_crono, T_progra, T_fase_ficha ,T_instru, T_acti_docu, T_perfil, T_compe, T_raps, T_DocumentFolder
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
from django.db.models import F

logger = logging.getLogger(__name__)

def fichas(request):
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
    fase = T_fase_ficha.objects.filter(ficha_id=ficha_id, vige=1).first()
    aprendices = T_apre.objects.filter(ficha=ficha_id)

    if request.method == 'GET':
        encuentro_form = EncuentroForm()
        actividad_form = ActividadForm()
        cronograma_form = CronogramaForm()
        raps_form = RapsFichaForm(ficha=ficha)
        encuentro_form = EncuentroForm()
        encuapre_form = EncuApreForm(ficha=ficha)
    
    return render(request, 'panel_ficha.html', {
        'ficha': ficha,
        'fase': fase,
        'aprendices': aprendices,
        'encuentro_form': encuentro_form,
        'actividad_form': actividad_form,
        'cronograma_form': cronograma_form,
        'raps_form': raps_form,
        'encuapre_form': encuapre_form

    })

@login_required
def obtener_estado_fase(request, ficha_id):
    fase = T_fase_ficha.objects.filter(ficha_id=ficha_id, vige=1).first()

    fase_vigente_subquery = T_fase_ficha.objects.filter(
        ficha_id=OuterRef('ficha_id'),
        vige='1'
    ).values('fase')[:1]

    raps_count = T_raps_ficha.objects.filter(
        ficha_id=ficha_id,
        agre='No',
        rap__compe__fase=Subquery(fase_vigente_subquery)
    ).count()

    raps_agregados = T_raps_ficha.objects.filter(
        ficha_id=ficha_id,
        agre='Si'
    ).values('rap_id')

    raps_pendientes_qs = T_raps_ficha.objects.filter(
        ficha_id=ficha_id,
        rap__compe__fase=Subquery(fase_vigente_subquery)
    ).exclude(
        rap_id__in=Subquery(
            T_raps_ficha.objects.filter(
                ficha_id=ficha_id,
                agre='Si'
            ).values('rap_id')
        )
    )

    tooltip_text = "<br>".join(f"{i+1}. {rap.rap.nom}" for i, rap in enumerate(raps_pendientes_qs))

    response = {
        'raps_count': raps_count,
        'raps_pendientes': tooltip_text,
        'fase': fase.fase,
    }
    return JsonResponse(response)


def cerrar_fase_ficha(request, ficha_id):
    if not ficha_id:
        return JsonResponse({"success": False, "error": "Falta el ID de la ficha."}, status=400)

    try:
        fase_actual = T_fase_ficha.objects.get(ficha_id=ficha_id, vige='1')
        FASES = ['analisis', 'planeacion', 'ejecucion', 'evaluacion']

        try:
            idx_actual = FASES.index(fase_actual.fase)
        except ValueError:
            return JsonResponse({"status": "error", "message": "Fase actual no reconocida."}, status=400)

        if fase_actual.fase == "evaluacion":
            return JsonResponse({
                "status": "error",
                "message": "No hay más fases para actualizar. Ya se encuentra en evaluación."
            }, status=400)

        # Cerrar la fase actual
        fase_actual.vige = '0'
        fase_actual.save()

        siguiente_fase = FASES[idx_actual + 1]

        # Verificar si la siguiente fase ya existe
        fase_siguiente_existente = T_fase_ficha.objects.filter(
            ficha_id=ficha_id,
            fase=siguiente_fase
        ).first()

        if fase_siguiente_existente:
            # Reactivar la fase existente
            fase_siguiente_existente.vige = '1'
            fase_siguiente_existente.fecha_ini = timezone.now()
            fase_siguiente_existente.save()
        else:
            # Crear nueva fase activa
            T_fase_ficha.objects.create(
                ficha_id=ficha_id,
                fase=siguiente_fase,
                vige='1',
                fecha_ini=timezone.now(),
                instru=None,
            )

        return JsonResponse({
            "success": True,
            "siguiente_fase": siguiente_fase,
            "message": f"Fase '{fase_actual.fase}' cerrada y nueva fase '{siguiente_fase}' activada."
        })

    except T_fase_ficha.DoesNotExist:
        return JsonResponse({"success": False, "error": "No se encontró la fase activa."}, status=404)

def devolver_fase_ficha(request, ficha_id):
    if not ficha_id:
        return JsonResponse({"status": "error", "message": "Falta el ID de la ficha."}, status=400)

    try:
        fase_actual = T_fase_ficha.objects.get(ficha_id=ficha_id, vige='1')
        FASES = ['analisis', 'planeacion', 'ejecucion', 'evaluacion']

        try:
            idx_actual = FASES.index(fase_actual.fase)
        except ValueError:
            return JsonResponse({"status": "error", "message": "Fase actual no reconocida."}, status=400)

        if idx_actual == 0:
            return JsonResponse({
                "status": "error",
                "message": "Ya está en la primera fase, no se puede devolver más."
            }, status=400)

        fase_anterior = FASES[idx_actual - 1]

        # Buscar fase anterior ya creada
        try:
            fase_anterior_reg = T_fase_ficha.objects.get(ficha_id=ficha_id, fase=fase_anterior)
        except T_fase_ficha.DoesNotExist:
            return JsonResponse({
                "status": "error",
                "message": f"No se encontró un registro previo para la fase '{fase_anterior}'."
            }, status=404)

        # Cerrar fase actual
        fase_actual.vige = '0'
        fase_actual.save()

        # Activar fase anterior
        fase_anterior_reg.vige = '1'
        fase_anterior_reg.save()

        return JsonResponse({
            "success": True,
            "fase_actual": fase_anterior,
            "message": f"Fase actual revertida a '{fase_anterior}'."
        })

    except T_fase_ficha.DoesNotExist:
        return JsonResponse({"success": False, "error": "No se encontró la fase activa."}, status=404)

def obtener_actividad(request, actividad_id):
    try:
        actividad_ficha = get_object_or_404(T_acti_ficha, id=actividad_id)
        actividad = actividad_ficha.acti
        raps_ids = list(
            T_raps_ficha.objects
            .filter(rap__t_raps_acti__acti=actividad)
            .values_list('id', flat=True)
            )
        data = {
            'nom': actividad.nom,
            'tipo': list(actividad.tipo.values_list('id', flat=True)),
            'descri': actividad.descri,
            'guia': actividad.guia_id,
            'fecha_ini_acti': actividad_ficha.crono.fecha_ini_acti.strftime('%Y-%m-%d'),
            'fecha_fin_acti': actividad_ficha.crono.fecha_fin_acti.strftime('%Y-%m-%d'),
            'fecha_ini_cali': actividad_ficha.crono.fecha_ini_cali.strftime('%Y-%m-%d'),
            'fecha_fin_cali': actividad_ficha.crono.fecha_fin_cali.strftime('%Y-%m-%d'),
            'nove': actividad_ficha.crono.nove,
            'raps': raps_ids,
        }

        return JsonResponse({'status': 'success', 'data': data})
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)

def obtener_carpetas(request, ficha_id):
    # Obtener todas las carpetas y documentos asociados a la ficha
    nodos = T_DocumentFolder.objects.filter(ficha_id=ficha_id).values(
        "id", "name", "parent_id", "tipo", "documento__id", "documento__nom", "documento__archi"
    )

    folder_map = {}

    for nodo in nodos:
        nodo_id = nodo["id"]
        parent_id = nodo["parent_id"]
        
        # Construcción del nodo base
        nodo_data = {
            "id": nodo_id,
            "name": nodo["name"],
            "parent_id": parent_id,
            "tipo": nodo["tipo"],
            "children": []
        }

        # Si es un documento, añadir los datos adicionales
        if nodo["tipo"] == "documento":
            nodo_data.update({
                "documento_id": nodo["documento__id"],
                "documento_nombre": nodo["documento__nom"],
                "url": nodo["documento__archi"],  # La URL del archivo
            })

        # Guardar en el mapa de nodos
        folder_map[nodo_id] = nodo_data

    root_nodes = []

    # Construcción de la jerarquía
    for nodo in folder_map.values():
        parent_id = nodo["parent_id"]
        if parent_id:
            if parent_id in folder_map:
                folder_map[parent_id]["children"].append(nodo)
        else:
            root_nodes.append(nodo)

    return JsonResponse(root_nodes, safe=False)

def cargar_documento(request):
    if request.method == 'POST':
        if  request.FILES.get("file"):
            file = request.FILES["file"]
            folder_id = request.POST.get("folder_id")

            folder = get_object_or_404(T_DocumentFolder, id = folder_id)

            # Generar la ruta de almacenamiento
            ruta = f'documentos/fichas/portafolio/{folder.ficha.id}/{file.name}'

            # Guardar el archivo
            ruta_guardada = default_storage.save(ruta, file)

            # Crear un nuevo registro en T_docu
            new_docu = T_docu.objects.create(
                nom=file.name,
                tipo= file.name.split('.')[-1],
                tama=f"{file.size // 1024} KB",
                archi=ruta_guardada,
                priva='No',
                esta='Activo'
            )

            # Crear un nuevo nodo de tipo "documento"
            document_node = T_DocumentFolder.objects.create(
                name=file.name,
                parent=folder,
                tipo="documento",
                ficha=folder.ficha,
                documento=new_docu
            )

            return JsonResponse({
                'status': 'success',
                'message': 'Documento cargado con éxito',
                'document': {
                    'id': document_node.id,
                    'name': document_node.name,
                    'url': new_docu.archi.url,
                    'folder_id': folder.id,
                    'tipo': 'documento'
                }
            }, status=200)
        return JsonResponse({'status': 'error', 'message': 'Debe cargar un documento'}, status = 400)
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status = 405)

@login_required  # Función para eliminar documento del portafolio
def eliminar_documento_portafolio_ficha(request, documento_id):
    if request.method != "DELETE":
        return JsonResponse({"status": "error", "error": "Método no permitido"}, status=405)

    documento = get_object_or_404(T_DocumentFolder, id=documento_id)

    if documento.documento:
        archivo_a_eliminar = documento.documento.archi.name
        documento.documento.delete()
        if archivo_a_eliminar:
            default_storage.delete(archivo_a_eliminar)

    documento.delete()

    return JsonResponse({"status": "success", "message": "Eliminado correctamente"}, status = 200)

def obtener_hijos_carpeta(request, carpeta_id):
    try:
        nodos = T_DocumentFolder.objects.filter(parent_id=carpeta_id).values(
            "id", "name", "parent_id", "tipo", "documento__id", "documento__nom", "documento__archi"
        )

        children = []

        for nodo in nodos:
            data = {
                "id": nodo["id"],
                "name": nodo["name"],
                "parent_id": nodo["parent_id"],
                "tipo": nodo["tipo"],
                "children": []
            }

            if nodo["tipo"] == "documento":
                data.update({
                    "documento_id": nodo["documento__id"],
                    "documento_nombre": nodo["documento__nom"],
                    "url": nodo["documento__archi"],
                })

            children.append(data)

        return JsonResponse(children, safe=False)

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

def obtener_carpetas_aprendiz(request, aprendiz_id):
    # Obtener todas las carpetas y documentos asociados a la ficha
    nodos = T_DocumentFolderAprendiz.objects.filter(aprendiz_id=aprendiz_id).values(
        "id", "name", "parent_id", "tipo", "documento__id", "documento__nom", "documento__archi"
    )

    folder_map = {}

    for nodo in nodos:
        nodo_id = nodo["id"]
        parent_id = nodo["parent_id"]
        
        # Construcción del nodo base
        nodo_data = {
            "id": nodo_id,
            "name": nodo["name"],
            "parent_id": parent_id,
            "tipo": nodo["tipo"],
            "children": []
        }

        # Si es un documento, añadir los datos adicionales
        if nodo["tipo"] == "documento":
            nodo_data.update({
                "documento_id": nodo["documento__id"],
                "documento_nombre": nodo["documento__nom"],
                "url": nodo["documento__archi"],  # La URL del archivo
            })

        # Guardar en el mapa de nodos
        folder_map[nodo_id] = nodo_data

    root_nodes = []

    # Construcción de la jerarquía
    for nodo in folder_map.values():
        parent_id = nodo["parent_id"]
        if parent_id:
            if parent_id in folder_map:
                folder_map[parent_id]["children"].append(nodo)
        else:
            root_nodes.append(nodo)

    return JsonResponse(root_nodes, safe=False)

def cargar_documento_aprendiz(request):
    if request.method == 'POST':
        if  request.FILES.get("file"):
            file = request.FILES["file"]
            folder_id = request.POST.get("folder_id")

            folder = get_object_or_404(T_DocumentFolderAprendiz, id = folder_id)

            # Generar la ruta de almacenamiento
            ruta = f'documentos/fichas/portafolio/aprendices/{folder.aprendiz.id}/{file.name}'

            # Guardar el archivo
            ruta_guardada = default_storage.save(ruta, file)

            # Crear un nuevo registro en T_docu
            new_docu = T_docu.objects.create(
                nom=file.name,
                tipo= file.name.split('.')[-1],
                tama=f"{file.size // 1024} KB",
                archi=ruta_guardada,
                priva='No',
                esta='Activo'
            )

            # Crear un nuevo nodo de tipo "documento"
            document_node = T_DocumentFolderAprendiz.objects.create(
                name=file.name,
                parent=folder,
                tipo="documento",
                aprendiz=folder.aprendiz,
                documento=new_docu
            )

            return JsonResponse({
                'status': 'success',
                'message': 'Documento cargado con éxito',
                'document': {
                    'id': document_node.id,
                    'name': document_node.name,
                    'url': new_docu.archi.url,
                    'folder_id': folder.id,
                    'tipo': 'documento'
                }
            }, status=200)
        return JsonResponse({'status': 'error', 'message': 'Debe cargar un documento'}, status = 400)
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status = 405)

@login_required
def eliminar_documento_portafolio_aprendiz(request, documento_id):
    if request.method != "DELETE":
        return JsonResponse({"status": "error", "error": "Método no permitido"}, status=405)

    documento = get_object_or_404(T_DocumentFolderAprendiz, id=documento_id)

    if documento.documento:
        archivo_a_eliminar = documento.documento.archi.name
        documento.documento.delete()
        if archivo_a_eliminar:
            default_storage.delete(archivo_a_eliminar)

    documento.delete()

    return JsonResponse({"status": "success", "message": "Eliminado correctamente"}, status = 200)

def obtener_hijos_carpeta_aprendiz(request, carpeta_id):
    try:
        nodos = T_DocumentFolderAprendiz.objects.filter(parent_id=carpeta_id).values(
            "id", "name", "parent_id", "tipo", "documento__id", "documento__nom", "documento__archi"
        )

        children = []

        for nodo in nodos:
            data = {
                "id": nodo["id"],
                "name": nodo["name"],
                "parent_id": nodo["parent_id"],
                "tipo": nodo["tipo"],
                "children": []
            }

            if nodo["tipo"] == "documento":
                data.update({
                    "documento_id": nodo["documento__id"],
                    "documento_nombre": nodo["documento__nom"],
                    "url": nodo["documento__archi"],
                })

            children.append(data)

        return JsonResponse(children, safe=False)

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@login_required
def crear_encuentro(request, ficha_id):
    logger.warning(request.POST)
    ficha = get_object_or_404(T_ficha, id=ficha_id)
    if request.method == 'POST':
        encuentro_form = EncuentroForm(request.POST)
        encuapre_form = EncuApreForm(request.POST, ficha=ficha)
        if encuentro_form.is_valid() and encuapre_form.is_valid():

            new_encuentro = encuentro_form.save(commit=False)
            new_encuentro.fecha = timezone.now()

            fase_ficha = T_fase_ficha.objects.filter(ficha=ficha, vige='1').first()

            new_encuentro.fase = fase_ficha
            new_encuentro.ficha = ficha
            new_encuentro.save()
            aprendices_seleccionados = encuapre_form.cleaned_data['aprendices']
            aprendices_ficha = T_apre.objects.filter(ficha=ficha)
            aprendices_seleccionados_set = set(aprendices_seleccionados)

            for aprendiz in aprendices_ficha:
                if aprendiz in aprendices_seleccionados_set:
                    T_encu_apre.objects.update_or_create(
                        encu=new_encuentro,  
                        apre=aprendiz,
                        defaults={'prese': 'No'}
                    )
                else:
                    T_encu_apre.objects.update_or_create(
                        encu=new_encuentro,  
                        apre=aprendiz,
                        defaults={'prese': 'Si'}
                    )

            for aprendiz_encu in aprendices_seleccionados:
                T_encu_apre.objects.update_or_create(
                    encu=new_encuentro,
                    apre=aprendiz_encu,
                    defaults={'prese': 'No'}
                )

            return JsonResponse ({'status': 'success', 'message': 'Encuentro creado con exito'}, status = 200)
        else: 
            errores_custom = []

            for field, errors_list in encuentro_form.errors.get_json_data().items():
                nombre_campo = encuentro_form.fields[field].label or field.capitalize()
                for err in errors_list:
                    errores_custom.append(f"<strong>{nombre_campo}</strong>: {err['message']}")

            for field, errors_list in encuapre_form.errors.get_json_data().items():
                nombre_campo = encuapre_form.fields[field].labels or field.capitalize()
                for err in errors_list:
                    errores_custom.append(f"<strong>{nombre_campo}</strong>: {err['message']}")

            return JsonResponse({'status': 'error', 'message': 'Errores en el formulario', 'errors': '<br>'.join(errores_custom)}, status=400)
    return JsonResponse ({'status':'error', 'message': 'Metodo no permitido'}, status = 405)

def obtener_encuentros(request, ficha_id):
    encuentros = T_encu.objects.filter(ficha_id = ficha_id)
    data = [
        {
            'id': encu.id,
            'fecha': encu.fecha,
            'tema': encu.tema,
            'lugar': encu.lugar
        } for encu in encuentros
    ]
    return JsonResponse(data, safe=False)

def obtener_actividades(request, ficha_id):
    actividades = T_acti_ficha.objects.filter(ficha_id = ficha_id)
    fase = T_fase_ficha.objects.filter(ficha_id = ficha_id, vige = 1).first()
    data = [
        {
            'id': actividad.id,
            'nom': actividad.acti.nom,
            'fecha_ini_acti': actividad.crono.fecha_ini_acti.strftime('%d/%m/%Y') if actividad.crono.fecha_ini_acti else '',
            'fecha_fin_acti': actividad.crono.fecha_fin_acti.strftime('%d/%m/%Y') if actividad.crono.fecha_fin_acti else '',
            'fecha_ini_cali': actividad.crono.fecha_ini_cali.strftime('%d/%m/%Y') if actividad.crono.fecha_ini_cali else '',
            'fecha_fin_cali': actividad.crono.fecha_fin_cali.strftime('%d/%m/%Y') if actividad.crono.fecha_fin_cali else '',
            'fase': actividad.acti.fase,
            'fase_ficha': fase.fase
        }
        for actividad in actividades
    ]

    return JsonResponse(data, safe=False)

@login_required
def crear_actividad(request, ficha_id):
    if request.method == 'POST':
        ficha = get_object_or_404(T_ficha, id=ficha_id)
        actividad_form = ActividadForm(request.POST)
        cronograma_form = CronogramaForm(request.POST)
        raps_form = RapsFichaForm(request.POST, ficha=ficha)

        if actividad_form.is_valid() and cronograma_form.is_valid() and raps_form.is_valid():
            

            # Creación de la actividad
            fase = T_fase_ficha.objects.filter(ficha_id=ficha_id, vige=1).first()
            new_actividad = actividad_form.save(commit=False)
            new_actividad.fase = fase.fase
            new_actividad.save()

            new_actividad.tipo.set(actividad_form.cleaned_data['tipo'])

            # # Creación del documento
            # archivo = documento_form.cleaned_data['archi']
            # nom = archivo.name
            # tipo = archivo.name.split('.')[-1]
            # tama = str(archivo.size // 1024) + " KB"
            # new_documento = documento_form.save(commit=False)
            # new_documento.nom = nom
            # new_documento.tipo = tipo
            # new_documento.tama = tama
            # new_documento.priva = 'No'
            # new_documento.esta = 'Activo'
            # new_documento.save()

            # Asignar la actividad al documento
            # T_acti_docu.objects.create(docu=new_documento, acti=new_actividad)

            # Creación del cronograma
            new_cronograma = cronograma_form.save()

            # Crear la actividad en T_acti_ficha
            new_acti_ficha = T_acti_ficha.objects.create(
                ficha=ficha,
                acti=new_actividad,
                crono=new_cronograma,
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
                    fecha= now()  # Fecha de asignación
                )

            raps_seleccionados = raps_form.cleaned_data['raps']

            # Crear los registros de raps seleccionados en T_raps_acti
            raps_seleccionados = raps_form.cleaned_data['raps']
            for rap_ficha in raps_seleccionados:
                T_raps_acti.objects.create(
                    rap=rap_ficha.rap,
                    acti=new_actividad
                )
                rap_ficha.agre = 'Si'
                rap_ficha.save()
            
            return JsonResponse({'status': 'success', 'message': 'Actividad creado con exito.'}, status = 200)
        else:
            errores_custom = []

            # Procesar errores de actividad_form
            for field, errors_list in actividad_form.errors.get_json_data().items():
                nombre_campo = actividad_form.fields[field].label or field.capitalize()
                for err in errors_list:
                    errores_custom.append(f"<strong>{nombre_campo}</strong>: {err['message']}")

            # Procesar errores de cronograma_form
            for field, errors_list in cronograma_form.errors.get_json_data().items():
                nombre_campo = cronograma_form.fields[field].label or field.capitalize()
                for err in errors_list:
                    errores_custom.append(f"<strong>{nombre_campo}</strong>: {err['message']}")

            # Procesar errores de raps_form (solo hay un campo: "raps")
            for field, errors_list in raps_form.errors.get_json_data().items():
                nombre_campo = raps_form.fields[field].label or field.capitalize()
                for err in errors_list:
                    errores_custom.append(f"<strong>{nombre_campo}</strong>: {err['message']}")

            # Devuelve todo como HTML con saltos de línea
            return JsonResponse({
                'status': 'error',
                'message': 'Errores en el formulario',
                'errors': '<br>'.join(errores_custom)
            }, status=400)
    return JsonResponse({'status': 'error', 'message': 'Metodo no permitido'}, status = 405)

def listar_actividades_ficha(request, ficha_id):
    
    actividades = T_acti_ficha.objects.select_related('crono', 'acti').filter(ficha_id = ficha_id)

    data = []
    for act in actividades:
        data.append({
            "title": act.acti.nom,
            "fase": act.acti.fase,
            "start": act.crono.fecha_ini_acti.isoformat(),
            "end": act.crono.fecha_fin_acti.isoformat(),
            "start_check": act.crono.fecha_ini_cali.isoformat(),
            "end_check": act.crono.fecha_fin_cali.isoformat()
        })

    return JsonResponse(data, safe=False)

def editar_actividad(request, actividad_id):
    actividad = get_object_or_404(T_acti_ficha, pk=actividad_id)

    if request.method == 'POST':
        form_actividad = ActividadForm(request.POST, instance=actividad.acti)
        form_cronograma = CronogramaForm(request.POST, instance=actividad.crono)
        form_raps = RapsFichaForm(request.POST, ficha = actividad.ficha)

        if form_actividad.is_valid() and form_cronograma.is_valid() and form_raps.is_valid():
            form_actividad.save()
            form_cronograma.save()

            raps_seleccionados = form_raps.cleaned_data['raps']

            T_raps_acti.objects.filter(acti=actividad.acti).delete()

            for rap_ficha in raps_seleccionados:
                T_raps_acti.objects.create(
                    rap=rap_ficha.rap,
                    acti=actividad.acti
                )

            raps_ficha = T_raps_ficha.objects.filter(ficha=actividad.ficha)

            for rap_ficha in raps_ficha:
                relaciones = T_raps_acti.objects.filter(rap=rap_ficha.rap, acti__t_acti_ficha__ficha=actividad.ficha)
                
                if relaciones.exists():
                    rap_ficha.agre = 'Si'
                else:
                    rap_ficha.agre = 'No'
                rap_ficha.save()

            return JsonResponse({'success': True, 'message': 'Actividad actualizada correctamente.'})
        else:
            errores = {
                'actividad': form_actividad.errors,
                'cronograma': form_cronograma.errors,
                'raps': form_raps.errors
            }
            return JsonResponse({'success': False, 'message': 'Error al actualizar la actividad.', 'errors': errores}, status=400)
    
    return JsonResponse({'success': False, 'message': 'Método no permitido.'}, status=405)

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

#Vistas Raps
def listar_guias(request):
    guias = T_guia.objects.all()
    return render(request, 'guias.html', {'guias': guias})

def crear_guia(request):
    if request.method == 'POST':
        guia_form = GuiaForm(request.POST)
        if guia_form.is_valid():
            guia_form.save()
            return redirect('raps')
    else:
        raps_form = RapsForm()
    return  render(request, 'crear_raps.html', {'raps_form': raps_form})

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

def calificarActividad(request):
    if request.method == 'POST':
        ids = request.POST.getlist('aprendiz_id[]')
        notas = request.POST.getlist('nota[]')
        actividad_id = int(request.POST.get('actividad_id'))

        try:
            actividad = T_acti_ficha.objects.get(id=actividad_id)
        except T_acti_ficha.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Actividad no encontrada'}, status=404)

        fecha_actual = now().date()
        if not (actividad.crono.fecha_ini_cali.date() <= fecha_actual <= actividad.crono.fecha_fin_cali.date()):
            return JsonResponse({
                'status': 'error',
                'message': 'La actividad no está dentro del período de calificación',
                'actividad_id': actividad_id
            }, status=400)

        for i in range(len(ids)):
            aprendiz_id = ids[i]
            nota = notas[i]

            aprendiz = T_apre.objects.get(id=aprendiz_id)

            T_cali.objects.update_or_create(
                apre=aprendiz,
                acti=actividad,
                defaults={'cali': nota}
            )
        return JsonResponse({'status': 'success', 'message': 'Calificado!', 'actividad_id': actividad_id}, status = 200)
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status = 405)

def obtener_aprendices_calificacion(request, ficha_id, actividad_id):
    
    aprendices = T_apre.objects.filter(ficha_id=ficha_id)
    respuesta = []

    for aprendiz in aprendices:
        cali = T_cali.objects.filter(
            apre_id=aprendiz.id, acti_id=actividad_id
        ).first()

        respuesta.append({
            'id': aprendiz.id,
            'nombre': aprendiz.perfil.nom,
            'apellido': aprendiz.perfil.apelli,
            'nota': cali.cali if cali else None
        })

    return JsonResponse(respuesta, safe=False)

def detalle_actividad(request, actividad_id):
    actividad_ficha = get_object_or_404(T_acti_ficha, id=actividad_id)
    actividad = actividad_ficha.acti
    crono = actividad_ficha.crono
    guia = actividad.guia
    tipos = list(actividad.tipo.values_list('tipo', flat=True))
    
    # RAPs desde la tabla personalizada T_raps_acti
    raps = list(
        T_raps_acti.objects.filter(acti=actividad)
        .select_related('rap__compe')
        .values('rap__id',
                'rap__nom',
                'rap__compe__fase',
                'rap__compe__nom'
        )
    )

    data = {
        "id": actividad.id,
        "nombre": actividad.nom,
        "descripcion": actividad.descri,
        "tipo_actividad": tipos,
        "fase": actividad.fase,
        "guia": {
            "id": guia.id,
            "nombre": guia.nom,
            "programa": guia.progra.nom,
            "horas_directas": guia.horas_dire,
            "horas_autonomas": guia.horas_auto
        },
        "cronograma": {
            "fecha_inicio_actividad": crono.fecha_ini_acti,
            "fecha_fin_actividad": crono.fecha_fin_acti,
            "fecha_inicio_calificacion": crono.fecha_ini_cali,
            "fecha_fin_calificacion": crono.fecha_fin_cali,
            "novedades": crono.nove
        },
        "raps": raps,
        # "descripciones": descripciones,
        "estado": actividad_ficha.esta,
        "ficha_id": actividad_ficha.ficha.id,
    }

    return JsonResponse(data, safe=False)

def detalle_programa(request, programa_id):
    programa = T_progra.objects.get(pk=programa_id)
    
    competencias = list(programa.t_compe_set.values('nom', 'fase'))
    guias = list(programa.t_guia_set.values('nom', 'horas_dire', 'horas_auto'))

    # RAPs asociados a todas las competencias del programa
    raps = []
    for compe in programa.t_compe_set.all():
        for rap in compe.t_raps_set.all():
            raps.append({'nom': rap.nom, 'fase': rap.fase})

    return JsonResponse({
        'cod_prog': programa.cod_prog,
        'nom': programa.nom,
        'nomd': programa.nomd,
        'competencias': competencias,
        'guias': guias,
        'raps': raps,
    })

def link_callback(uri, rel):
    result = finders.find(uri.replace(settings.STATIC_URL, ""))
    if result:
        return result
    raise Exception(f"Media URI must start with {settings.STATIC_URL}")

def generar_acta_asistencia(request):
    ficha_id = request.GET.get('ficha_id')
    formato  = request.GET.get('formato')

    ficha = T_ficha.objects.get(id=ficha_id)
    encuentros = T_encu.objects.filter(ficha=ficha).order_by('fecha')
    aprendices = T_apre.objects.filter(ficha=ficha)

    asistencias = {
        apre.id: {
            encu.id: "No"
            for encu in encuentros
        } for apre in aprendices
    }

    registros = T_encu_apre.objects.filter(encu__in=encuentros, apre__in=aprendices)

    for reg in registros:
        asistencias[reg.apre.id][reg.encu.id] = reg.prese

    if formato == 'pdf':
        template = get_template("reportes/acta_asistencia_general.html")
        tabla = []
        for apre in aprendices:
            fila = {
                'apre': apre,
                'asistencias': []
            }
            for encu in encuentros:
                prese = asistencias.get(apre.id, {}).get(encu.id, "No")
                fila['asistencias'].append("Sí" if prese == "Si" else "No")
            tabla.append(fila)
        html = template.render({
            'logo_url': settings.STATIC_URL + 'images/imagenhome.png',
            'tabla': tabla,
            'ficha': ficha,
            'encuentros': encuentros,
            'aprendices': aprendices,
            'asistencias': asistencias,
        })
        buffer = BytesIO()
        pisa.CreatePDF(html, dest=buffer, link_callback=link_callback)
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename=f"Acta_Asistencia_{ficha.id}.pdf")

    elif formato == 'excel':
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Asistencia"

        # Encabezado
        ws.cell(row=1, column=1).value = "Aprendiz"
        for col, encu in enumerate(encuentros, start=2):
            ws.cell(row=1, column=col).value = encu.fecha.strftime('%d/%m/%Y')

        # Filas
        for row, apre in enumerate(aprendices, start=2):
            ws.cell(row=row, column=1).value = f"{apre.perfil.nom} {apre.perfil.apelli}"
            for col, encu in enumerate(encuentros, start=2):
                valor = asistencias[apre.id][encu.id]
                ws.cell(row=row, column=col).value = "Sí" if valor == "Si" else "No"
        # Descargar
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename=f"Asistencia_{ficha.id}.xlsx")
    return HttpResponse("Formato no válido", status=400)

def generar_acta_asistencia_aprendiz(request):
    aprendiz_id = request.GET.get('aprendiz_id')
    aprendiz = T_apre.objects.get(id=aprendiz_id)
    asistencias = T_encu_apre.objects.filter(apre=aprendiz)

    context = {
        'aprendiz': aprendiz,
        'asistencias': asistencias
    }

    template = get_template("reportes/acta_asistencia_aprendiz.html")
    html = template.render({
        'aprendiz': aprendiz,
        'asistencias': asistencias,
    })

    buffer = BytesIO()
    pisa.CreatePDF(html, dest=buffer)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"Acta_Asistencia_{aprendiz.perfil.nom}_{aprendiz.perfil.apelli}.pdf")

def generar_informe_calificaciones(request):
    ficha_id = request.GET.get('ficha_id')
    formato  = request.GET.get('formato')

    ficha = T_ficha.objects.get(id=ficha_id)
    actividades = T_acti_ficha.objects.filter(ficha=ficha).order_by('id')
    aprendices = T_apre.objects.filter(ficha=ficha)

    # Diccionario: aprendiz_id -> {actividad_id: "Aprobó"/"No aprobó"}
    calificaciones = {
        apre.id: {
            acti.id: ""
            for acti in actividades
        } for apre in aprendices
    }

    registros = T_cali.objects.filter(apre__in=aprendices, acti__in=actividades)

    for cali in registros:
        estado = "Aprobó" if int(cali.cali) == 1 else "No aprobó"
        calificaciones[cali.apre.id][cali.acti.id] = estado

    if formato == 'pdf':
        template = get_template("reportes/informe_calificaciones.html")
        tabla = []
        for apre in aprendices:
            fila = {
                'apre': apre,
                'calificaciones': [calificaciones[apre.id][acti.id] for acti in actividades]
            }
            tabla.append(fila)
        html = template.render({
            'logo_url': settings.STATIC_URL + 'images/imagenhome.png',
            'tabla': tabla,
            'ficha': ficha,
            'actividades': actividades,
            'aprendices': aprendices
        })
        buffer = BytesIO()
        pisa.CreatePDF(html, dest=buffer, link_callback=link_callback)
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename=f"Informe_Calificaciones_{ficha.id}.pdf")

    elif formato == 'excel':
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Calificaciones"

        # Encabezado
        ws.cell(row=1, column=1).value = "Aprendiz"
        for col, acti in enumerate(actividades, start=2):
            ws.cell(row=1, column=col).value = acti.acti.nom

        # Filas
        for row, apre in enumerate(aprendices, start=2):
            ws.cell(row=row, column=1).value = f"{apre.perfil.nom} {apre.perfil.apelli}"
            for col, acti in enumerate(actividades, start=2):
                estado = calificaciones[apre.id][acti.id]
                ws.cell(row=row, column=col).value = estado

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename=f"Informe_Calificaciones_{ficha.id}.xlsx")

    return HttpResponse("Formato no válido", status=400)

def detalle_encuentro(request, encuentro_id):
    encuentro = T_encu.objects.get(id = encuentro_id)

    total_aparticipantes = T_encu_apre.objects.filter(encu= encuentro).count()

    asistencias = T_encu_apre.objects.filter(encu = encuentro)

    aprendices_asistieron = []
    aprendices_faltaron = []

    for asistencia in asistencias:
        aprendiz = asistencia.apre
        aprendiz_data = {
            'id': aprendiz.id,
            'nombre': f"{aprendiz.perfil.nom} {aprendiz.perfil.apelli}"
        }
        if asistencia.prese == "Si":
            aprendices_asistieron.append(aprendiz_data)
        elif asistencia.prese == "No":
            aprendices_faltaron.append(aprendiz_data)

    data = {
        'lugar': encuentro.lugar,
        'fecha': encuentro.fecha.strftime('%Y-%m-%d'),
        'participantes': total_aparticipantes,
        'aprendicesAsistieron': aprendices_asistieron,
        'aprendicesFaltaron': aprendices_faltaron
    }

    return JsonResponse({'status': 'success', 'message': 'Datos retornados con exito', 'data': data}, status = 200)