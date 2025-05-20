from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST, require_GET
from django.db import transaction
from django.contrib.staticfiles import finders
import openpyxl
import logging
from django.http import FileResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from django.utils import timezone 
from django.db.models import Subquery, OuterRef, Exists
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from .forms import CascadaMunicipioInstitucionForm,GuiaForm, CargarDocuPortafolioFichaForm, ActividadForm,RapsFichaForm, EncuApreForm, EncuentroForm, DocumentosForm, CronogramaForm, ProgramaForm, CompetenciaForm, RapsForm, FichaForm
from commons.models import T_encu,T_compe_progra, T_fase, T_centro_forma,T_guia, T_cali, T_prematri_docu ,T_docu, T_munici, T_insti_edu, T_acti_apre,T_raps_acti,T_perfil, T_DocumentFolderAprendiz, T_encu_apre, T_apre, T_raps_ficha, T_acti_ficha, T_ficha, T_crono, T_progra, T_fase_ficha ,T_instru, T_acti_docu, T_perfil, T_compe, T_raps, T_DocumentFolder
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
    fase_ficha = T_fase_ficha.objects.filter(ficha_id=ficha_id, vige=1).first()
    if not fase_ficha:
        return JsonResponse({
            'raps_count': 0,
            'raps_pendientes': '',
            'fase': 'Sin fase activa'
        })

    fase_id = fase_ficha.fase.id

    raps_pendientes = (
        T_raps_ficha.objects
        .filter(
            ficha_id=ficha_id,
            fase_id=fase_id,
            agre='No'
        )
        .values('rap_id', 'rap__nom')
        .distinct()
    )

    raps_count = raps_pendientes.count()
    tooltip_text = "<br>".join(f"{i+1}. {rap['rap__nom']}" for i, rap in enumerate(raps_pendientes))

    return JsonResponse({
        'raps_count': raps_count,
        'raps_pendientes': tooltip_text,
        'fase': fase_ficha.fase.nom
    })



def cerrar_fase_ficha(request, ficha_id):
    if not ficha_id:
        return JsonResponse({"success": False, "error": "Falta el ID de la ficha."}, status=400)

    try:
        fase_actual = T_fase_ficha.objects.get(ficha_id=ficha_id, vige='1')
        fase_actual_id = fase_actual.fase.id

        if fase_actual_id >= 4:
            return JsonResponse({
                "status": "error",
                "message": "No hay más fases para actualizar. Ya se encuentra en evaluación."
            }, status=400)

        # Cerrar la fase actual
        fase_actual.vige = '0'
        fase_actual.save()

        siguiente_fase_id = fase_actual_id + 1
        siguiente_fase_obj = T_fase.objects.get(id=siguiente_fase_id)

        # Verificar si la siguiente fase ya existe
        fase_siguiente_existente = T_fase_ficha.objects.filter(
            ficha_id=ficha_id,
            fase=siguiente_fase_obj
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
                fase=siguiente_fase_obj,
                vige='1',
                fecha_ini=timezone.now(),
                instru=None,
            )

        return JsonResponse({
            "success": True,
            "siguiente_fase": siguiente_fase_obj.nom,
            "message": f"Fase '{fase_actual.fase.nom}' cerrada y nueva fase '{siguiente_fase_obj.nom}' activada."
        })

    except T_fase_ficha.DoesNotExist:
        return JsonResponse({"success": False, "error": "No se encontró la fase activa."}, status=404)
    except T_fase.DoesNotExist:
        return JsonResponse({"success": False, "error": "Fase siguiente no existe en T_fase."}, status=404)


def devolver_fase_ficha(request, ficha_id):
    if not ficha_id:
        return JsonResponse({"status": "error", "message": "Falta el ID de la ficha."}, status=400)

    try:
        fase_actual = T_fase_ficha.objects.get(ficha_id=ficha_id, vige='1')
        fase_actual_id = fase_actual.fase.id

        if fase_actual_id <= 1:
            return JsonResponse({
                "status": "error",
                "message": "Ya está en la primera fase, no se puede devolver más."
            }, status=400)

        fase_anterior_id = fase_actual_id - 1

        try:
            fase_anterior_obj = T_fase.objects.get(id=fase_anterior_id)
        except T_fase.DoesNotExist:
            return JsonResponse({
                "status": "error",
                "message": f"No se encontró definición de fase con ID {fase_anterior_id} en T_fase."
            }, status=404)

        try:
            fase_anterior_reg = T_fase_ficha.objects.get(ficha_id=ficha_id, fase=fase_anterior_obj)
        except T_fase_ficha.DoesNotExist:
            return JsonResponse({
                "status": "error",
                "message": f"No se encontró un registro previo para la fase '{fase_anterior_obj.nom}'."
            }, status=404)

        # Cerrar fase actual
        fase_actual.vige = '0'
        fase_actual.save()

        # Activar fase anterior
        fase_anterior_reg.vige = '1'
        fase_anterior_reg.save()

        return JsonResponse({
            "success": True,
            "fase_actual": fase_anterior_obj.nom,
            "message": f"Fase actual revertida a '{fase_anterior_obj.nom}'."
        })

    except T_fase_ficha.DoesNotExist:
        return JsonResponse({"success": False, "error": "No se encontró la fase activa."}, status=404)

def obtener_actividad(request, actividad_id):
    try:
        actividad_ficha = get_object_or_404(T_acti_ficha, id=actividad_id)
        actividad = actividad_ficha.acti

        raps_ids = list(
            T_raps_ficha.objects
            .filter(t_raps_acti__acti=actividad)
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
        import traceback
        traceback.print_exc()
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
            'fase': actividad.acti.fase.nom,
            'fase_ficha': fase.fase.nom
        }
        for actividad in actividades
    ]

    return JsonResponse(data, safe=False)

@login_required
def crear_actividad(request, ficha_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    ficha = get_object_or_404(T_ficha, id=ficha_id)
    actividad_form = ActividadForm(request.POST)
    cronograma_form = CronogramaForm(request.POST)
    raps_form = RapsFichaForm(request.POST, ficha=ficha)

    if not (actividad_form.is_valid() and cronograma_form.is_valid() and raps_form.is_valid()):
        errores_custom = []

        def agregar_errores(form):
            for field, errors_list in form.errors.get_json_data().items():
                nombre_campo = form.fields[field].label or field.capitalize()
                for err in errors_list:
                    errores_custom.append(f"<strong>{nombre_campo}</strong>: {err['message']}")

        agregar_errores(actividad_form)
        agregar_errores(cronograma_form)
        agregar_errores(raps_form)

        return JsonResponse({
            'status': 'error',
            'message': 'Errores en el formulario',
            'errors': '<br>'.join(errores_custom)
        }, status=400)

    # Si llegamos aquí, todos los formularios son válidos
    with transaction.atomic():
        # Obtener la fase activa vinculada a la ficha
        fase = T_fase_ficha.objects.filter(ficha_id=ficha_id, vige=1).first()
        if not fase:
            return JsonResponse({'status': 'error', 'message': 'No se encontró fase activa para la ficha.'}, status=400)

        # Crear actividad sin guardar aún para asignar fase
        new_actividad = actividad_form.save(commit=False)
        new_actividad.fase = fase.fase
        new_actividad.save()
        new_actividad.tipo.set(actividad_form.cleaned_data['tipo'])

        # Crear cronograma
        new_cronograma = cronograma_form.save()

        # Crear relación actividad-ficha-cronograma
        new_acti_ficha = T_acti_ficha.objects.create(
            ficha=ficha,
            acti=new_actividad,
            crono=new_cronograma,
            esta='Activo'
        )

        # Crear registros para aprendices con estado inicial y fecha actual
        aprendices = T_apre.objects.filter(ficha=ficha)
        for aprendiz in aprendices:
            T_acti_apre.objects.create(
                apre=aprendiz,
                acti=new_acti_ficha,
                apro='Pendiente',
                fecha=now()
            )

        # Guardar raps seleccionados y marcar agre = 'Si'
        raps_seleccionados = raps_form.cleaned_data['raps']

        for rap_ficha in raps_seleccionados:
            # Verifica que el RAP esté asociado a la fase actual
            rap_ficha_fase = T_raps_ficha.objects.filter(
                ficha=ficha,
                rap=rap_ficha.rap,
                fase=fase.fase  # fase actual
            ).first()

            if rap_ficha_fase:
                # Crear relación actividad - rap
                T_raps_acti.objects.create(
                    rap=rap_ficha,
                    acti=new_actividad
                )
                # Marcar como agregado solo el registro correspondiente a esta fase
                rap_ficha_fase.agre = 'Si'
                rap_ficha_fase.save()


    return JsonResponse({'status': 'success', 'message': 'Actividad creada con éxito.'}, status=200)

def listar_actividades_ficha(request, ficha_id):
    
    actividades = T_acti_ficha.objects.select_related('crono', 'acti').filter(ficha_id = ficha_id)

    data = []
    for act in actividades:
        data.append({
            "title": act.acti.nom,
            "fase": act.acti.fase.nom,
            "start": act.crono.fecha_ini_acti.isoformat(),
            "end": act.crono.fecha_fin_acti.isoformat(),
            "start_check": act.crono.fecha_ini_cali.isoformat(),
            "end_check": act.crono.fecha_fin_cali.isoformat()
        })

    return JsonResponse(data, safe=False)

@login_required
def editar_actividad(request, actividad_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido.'}, status=405)

    actividad = get_object_or_404(T_acti_ficha, pk=actividad_id)
    ficha = actividad.ficha

    form_actividad = ActividadForm(request.POST, instance=actividad.acti)
    form_cronograma = CronogramaForm(request.POST, instance=actividad.crono)
    form_raps = RapsFichaForm(request.POST, ficha=ficha)

    if form_actividad.is_valid() and form_cronograma.is_valid() and form_raps.is_valid():
        try:
            with transaction.atomic():
                # Guardar actividad y cronograma
                form_actividad.save()
                form_cronograma.save()

                # Limpiar relaciones anteriores
                T_raps_acti.objects.filter(acti=actividad.acti).delete()

                # Crear nuevas relaciones
                raps_seleccionados = form_raps.cleaned_data['raps']
                for rap_ficha in raps_seleccionados:
                    T_raps_acti.objects.create(
                        rap=rap_ficha,
                        acti=actividad.acti
                    )

                # Actualizar el campo agre
                raps_ficha = T_raps_ficha.objects.filter(ficha=ficha)
                for rap_ficha in raps_ficha:
                    tiene_relaciones = T_raps_acti.objects.filter(
                        rap=rap_ficha,
                        acti__t_acti_ficha__ficha=ficha
                    ).exists()
                    rap_ficha.agre = 'Si' if tiene_relaciones else 'No'
                    rap_ficha.save()

            return JsonResponse({'success': True, 'message': 'Actividad actualizada correctamente.'})

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'message': 'Error interno al actualizar la actividad.',
                'error': str(e)
            }, status=500)

    # Si los formularios no son válidos
    errores = {}
    for form_name, form_obj in [('actividad', form_actividad), ('cronograma', form_cronograma), ('raps', form_raps)]:
        errores[form_name] = form_obj.errors.get_json_data()

    return JsonResponse({
        'success': False,
        'message': 'Error al actualizar la actividad.',
        'errors': errores
    }, status=400)

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

###############################################################################################################
#        VISTAS COMPETENCIA
###############################################################################################################

def competencias(request):
    competencia_form = CompetenciaForm()
    return render(request, 'competencias.html', {
        'competencia_form': competencia_form
        })

def crear_competencia(request):
    if request.method == 'POST':
        competencia_form = CompetenciaForm(request.POST)
        if competencia_form.is_valid():
            nombre = competencia_form.cleaned_data['nom']
            if T_compe.objects.filter(nom = nombre).exists():
                return JsonResponse({'status': 'error', 'message': 'Ya existe una competencia con el nombre indicado'}, status = 400)
            
            competencia_form.save()
            return JsonResponse({'status': 'error', 'message': 'Competencia creada'}, status = 200)
    return JsonResponse({'status': 'error', 'message': 'Metodo no permitido'}, status =  405)

def filtrar_competencias(request):
    if request.method == 'GET':
        programa = request.GET.getlist('programas', [])
        fase = request.GET.getlist('fases', [])

        competencias = T_compe.objects.all()

        if programa:
            competencias = competencias.filter(progra__nom__in = programa)
        if fase:
            competencias = competencias.filter(fase__nom__in = fase)
        
        data = [
            {
                'id': c.id,
                'nom': c.nom,
                'fase': [f.nom for f in c.fase.all()],
                'progra': [p.nom for p in c.progra.all()]
            } for c in competencias
        ]
        return JsonResponse(data, safe=False)

    return JsonResponse({'status': 'error', 'message': 'Metodo no permitido'}, status = 405)

def obtener_opciones_fases(request):
    fases = T_fase.objects.filter(t_compe_fase__isnull=False).distinct().values_list('nom')
    return JsonResponse(list(fases), safe=False)

def obtener_opciones_programas(request):
    programas = T_progra.objects.filter(t_compe_progra__isnull=False).distinct().values_list('nom')
    return JsonResponse(list(programas), safe=False)

def obtener_competencia(request, competencia_id):
    competencia = T_compe.objects.filter(pk=competencia_id).first()
    if competencia:
        data = {
            'id': competencia.id,
            'nom': competencia.nom,
            'progra': list(competencia.progra.values_list('id', flat=True)),
            'fase': list(competencia.fase.values_list('id', flat=True))
        }
        return JsonResponse(data)
    return JsonResponse({'status': 'error', 'message': 'Competencia no encontrada'}, status=404)


def editar_competencia(request, competencia_id):
    competencia = T_compe.objects.filter(pk = competencia_id).first()

    if request.method == 'POST':
        form_competencia = CompetenciaForm(request.POST, instance=competencia)
        
        if form_competencia.is_valid():
            nombre = form_competencia.cleaned_data['nom']
            if T_compe.objects.filter(nom=nombre).exclude(pk=competencia_id).exists():
                return JsonResponse({'status': 'error', 'message': 'Ya existe una competencia con el nombre indicado'}, status = 400)

            form_competencia.save()
            return JsonResponse({'status': 'success', 'message': 'Competencia actualizada con exito.'}, status = 200)
        else:
            return JsonResponse({'status': 'error', 'message': 'Error al actualizar la competencia', 'errors': form_competencia.errors}, status=400) 
    return JsonResponse({'status': 'error', 'message': 'Metodo no permitido'}, status = 405)

###############################################################################################################
#        VISTAS RAPS
###############################################################################################################

def listar_raps(request):
    rap_form = RapsForm()
    programas = T_progra.objects.filter(
        Exists(
            T_compe_progra.objects.filter(progra=OuterRef('pk'))
        )
    )
    
    return render(request, 'raps.html', {
        'rap_form': rap_form,
        'programas': programas,
        })

def crear_rap(request):
    rap_form = RapsForm(request.POST)

    if rap_form.is_valid():
        nombre = rap_form.cleaned_data['nom']
        if T_raps.objects.filter(nom=nombre).exists():
            return JsonResponse({'status': 'error', 'message': 'Ya existe un RAP con el nombre indicado'}, status=400)

        # Obtener la competencia desde el select manual
        compe_id = request.POST.get('compe')
        if not compe_id:
            return JsonResponse({'status': 'error', 'message': 'Debe seleccionar una competencia'}, status=400)

        try:
            competencia = T_compe.objects.get(id=compe_id)
        except T_compe_progra.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Competencia no encontrada'}, status=404)

        # Crear el RAP manualmente
        nuevo_rap = rap_form.save(commit=False)
        nuevo_rap.compe = competencia
        nuevo_rap.comple="No"
        nuevo_rap.save()

        return JsonResponse({'status': 'success', 'message': 'RAP creado correctamente'}, status=200)

    return JsonResponse({'status': 'error', 'message': 'Formulario inválido', 'errors': rap_form.errors}, status=400)

def filtrar_raps(request):
    if request.method == 'GET':
        programas = request.GET.getlist('programas', [])
        fases = request.GET.getlist('fases', [])
        competencias = request.GET.getlist('competencias', [])

        raps = T_raps.objects.select_related('compe').prefetch_related('compe__progra', 'compe__fase')

        if programas:
            raps = raps.filter(compe__progra__nom__in=programas)
        if fases:
            raps = raps.filter(compe__fase__nom__in=fases)
        if competencias:
            raps = raps.filter(compe__nom__in=competencias)

        data = []
        for rap in raps:
            compe = rap.compe
            fases = list(compe.fase.values_list('nom', flat=True)) if compe else []
            programas = list(compe.progra.values_list('nom', flat=True)) if compe else []

            data.append({
                'id': rap.id,
                'nom': rap.nom,
                'fase': ', '.join(fases) if fases else None,
                'competencia': compe.nom if compe else None,
                'programa': ', '.join(programas) if programas else None
            })

        return JsonResponse(data, safe=False)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

def obtener_opciones_fases_raps(request):
    fases = T_fase.objects.filter(
        t_compe_fase__compe__t_raps__isnull=False
    ).distinct().values_list('nom', flat=True)

    return JsonResponse(list(fases), safe=False)

def obtener_opciones_programas_raps(request):
    programas = T_progra.objects.filter(
        t_compe_progra__compe__t_raps__isnull=False
    ).distinct().values_list('nom', flat=True)

    return JsonResponse(list(programas), safe=False)

def obtener_opciones_competencias_raps(request):
    competencias = T_compe.objects.filter(
        t_raps__isnull=False
    ).distinct().values_list('nom', flat=True)

    return JsonResponse(list(competencias), safe=False)

def obtener_competencias_programa(request, id_progra):
    competencias = T_compe_progra.objects.filter(progra_id = id_progra).distinct()
    data = list(competencias.values('compe__id', 'compe__nom'))
    return JsonResponse(data, safe=False)

def obtener_rap(request, rap_id):
    rap = T_raps.objects.filter(pk=rap_id).first()
    if rap:
        data = {
            'id': rap.id,
            'nom': rap.nom,
            'compe': rap.compe.id
        }
        return JsonResponse(data)
    return JsonResponse({'status': 'error', 'message': 'RAP no encontrado'}, status=404)

def obtener_opciones_competencias(request):
    competencias = T_compe.objects.all().values('id', 'nom')
    return JsonResponse(list(competencias), safe=False)

def editar_rap(request, rap_id):
    rap = T_raps.objects.filter(pk = rap_id).first()

    if request.method == 'POST':
        form_rap = RapsForm(request.POST, instance = rap)

        if form_rap.is_valid():
            nom = form_rap.cleaned_data['nom']
            if T_raps.objects.filter(nom = nom).exclude(pk=rap_id).exists():
                return JsonResponse({'status': 'error', 'message': 'Ya existe un RAP con el nombre indicado'}, status = 400)
            form_rap.save();
            return JsonResponse({'status': 'success', 'message': 'RAP actualizado con exito'}, status = 200)
        else:
            return JsonResponse({'status': 'error', 'message': 'Error al actualizar la competencia', 'errors': form_rap.errors}, status = 400)
    return JsonResponse({'status': 'error', 'message': 'metodo no permitido'}, status = 405)

###############################################################################################################
#        VISTAS GUIAS
###############################################################################################################

def listar_guias(request):
    guia_form = GuiaForm()
    guias = T_guia.objects.all()
    return render(request, 'guias.html', {
        'guias': guias,
        'guia_form': guia_form
        })

def crear_guia(request):
    if request.method == 'POST':
        guia_form = GuiaForm(request.POST)
        if guia_form.is_valid():
            guia_form.save()
            return JsonResponse({'status': 'success', 'message': 'Guia creada'}, status = 200)
    return JsonResponse({'status': 'error', 'message': 'Metodo no permitido'}, status = 405)

@require_GET
def obtener_guia(request, guia_id):
    guia = T_guia.objects.filter(pk=guia_id).first()
    if not guia:
        return JsonResponse({'status': 'error', 'message': 'Guia no encontrada'}, status=404)
    
    data = {
        'id': guia.id,
        'nom': guia.nom,
        'horas_auto': guia.horas_auto,
        'horas_dire': guia.horas_dire,
        'progra': guia.progra.id
    }

    return JsonResponse(data)

@require_POST
def editar_guia(request, guia_id):
    guia = T_guia.objects.filter(pk=guia_id).first()
    if not guia:
        return JsonResponse({'status': 'error', 'message': 'Guia no encontrada'}, status=404)
    
    form_guia = GuiaForm(request.POST, instance=guia)

    if form_guia.is_valid():
        form_guia.save()
        return JsonResponse({'status': 'success', 'message': 'Guia actualizada con exito'}, status = 200)
    return JsonResponse({'status': 'error', 'message': 'Error al actualizar la guia', 'errors': form_guia.errors}, status=400)


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
        .values(
            'rap__rap__id',
            'rap__rap__nom',
            'rap__rap__compe__fase',
            'rap__rap__compe__fase__nom',
            'rap__rap__compe__nom'
        )
    )

    data = {
        "id": actividad.id,
        "nombre": actividad.nom,
        "descripcion": actividad.descri,
        "tipo_actividad": tipos,
        "fase": actividad.fase.nom,
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

    competencias = []
    for compe in T_compe.objects.filter(progra=programa):
        fases = T_fase.objects.filter(t_compe_fase__compe=compe).values_list('nom', flat=True)
        competencias.append({
            'nom': compe.nom,
            'fase': list(fases),
        })

    guias = list(programa.t_guia_set.values('nom', 'horas_dire', 'horas_auto'))

    raps = []
    for compe in T_compe.objects.filter(progra=programa):
        for rap in compe.t_raps_set.all():
            raps.append({
                'nom': rap.nom,
                'compe': compe.nom,  # para que sepas a qué competencia pertenece
            })

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