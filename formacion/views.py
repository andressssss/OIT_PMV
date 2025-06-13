from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST, require_GET
from matricula.scripts.cargar_tree import crear_datos_prueba 
from matricula.scripts.cargar_tree_apre import crear_datos_prueba_aprendiz
from django.db import transaction
from django.contrib.staticfiles import finders
from django.utils.encoding import force_str
import io
import zipfile
import os
import openpyxl
import csv
import random
import string
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from django.db.models import Q
import logging
from django.http import FileResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from django.utils import timezone 
from django.db.models import Subquery, OuterRef, Exists
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from .forms import CascadaMunicipioInstitucionForm,GuiaForm, CargarFichasMasivoForm, CargarDocuPortafolioFichaForm, ActividadForm,RapsFichaForm, EncuApreForm, EncuentroForm, DocumentosForm, CronogramaForm, ProgramaForm, CompetenciaForm, RapsForm, FichaForm
from commons.models import T_encu,T_departa, T_munici, T_compe_progra,T_gestor_depa, T_fase, T_centro_forma,T_guia, T_cali, T_prematri_docu ,T_docu, T_munici, T_insti_edu, T_acti_apre,T_raps_acti,T_perfil, T_DocumentFolderAprendiz, T_encu_apre, T_apre, T_raps_ficha, T_acti_ficha, T_ficha, T_crono, T_progra, T_fase_ficha ,T_instru, T_acti_docu, T_perfil, T_compe, T_raps, T_DocumentFolder, T_repre_legal, T_grupo, T_gestor, T_gestor_grupo
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.conf import settings
from django.core.files.storage import default_storage
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import F
from io import TextIOWrapper
from django.forms import ValidationError
from django.core.validators import validate_email

logger = logging.getLogger(__name__)

###############################################################################################################
#        VISTAS FICHA
###############################################################################################################
@login_required
def fichas(request):
    fichas = T_ficha.objects.all()
    return render(request, 'listar_fichas.html', {'fichas': fichas})

@require_GET
@login_required
def obtener_opciones_fichas_estados(request):
    perfil_logueado = T_perfil.objects.get(user=request.user)

    fichas = T_ficha.objects.filter(esta__isnull=False)

    if perfil_logueado.rol == "gestor":
        gestor = T_gestor.objects.get(perfil=perfil_logueado)
        departamentos = T_gestor_depa.objects.filter(gestor=gestor).values_list('depa__nom_departa', flat=True)
        fichas = fichas.filter(insti__muni__nom_departa__nom_departa__in=departamentos)

    estados = fichas.distinct().values_list('esta', flat=True)
    return JsonResponse(list(estados), safe=False)


@require_GET
@login_required
def obtener_opciones_fichas_instructores(request):
    perfil_logueado = T_perfil.objects.get(user=request.user)

    if perfil_logueado.rol == "instructor":
        return JsonResponse([perfil_logueado.nom], safe=False)

    fichas = T_ficha.objects.filter(instru__isnull=False)

    if perfil_logueado.rol == "gestor":
        gestor = T_gestor.objects.get(perfil=perfil_logueado)
        departamentos = T_gestor_depa.objects.filter(gestor=gestor).values_list('depa__nom_departa', flat=True)
        fichas = fichas.filter(insti__muni__nom_departa__nom_departa__in=departamentos)

    instructores = fichas.distinct().values_list('instru__perfil__nom', flat=True)
    opciones = ['Sin asignar'] + list(instructores)
    return JsonResponse(opciones, safe=False)


@require_GET
@login_required
def obtener_opciones_fichas_programas(request):
    perfil_logueado = T_perfil.objects.get(user=request.user)

    fichas = T_ficha.objects.filter(progra__isnull=False)

    if perfil_logueado.rol == "gestor":
        gestor = T_gestor.objects.get(perfil=perfil_logueado)
        departamentos = T_gestor_depa.objects.filter(gestor=gestor).values_list('depa__nom_departa', flat=True)
        fichas = fichas.filter(insti__muni__nom_departa__nom_departa__in=departamentos)

    programas = fichas.distinct().values_list('progra__nom', flat=True)
    return JsonResponse(list(programas), safe=False)


@require_GET
@login_required
def filtrar_fichas(request):
    perfil_logueado = T_perfil.objects.get(user = request.user)
    estados = request.GET.getlist('estados', [])
    instructores = request.GET.getlist('instructores', [])
    programas = request.GET.getlist('programas', [])

    fichas = T_ficha.objects.all()

    if perfil_logueado.rol == "instructor":
        instructor = T_instru.objects.get(perfil = perfil_logueado)
        fichas = fichas.filter(instru = instructor)
    elif perfil_logueado.rol == "gestor":
        gestor = T_gestor.objects.get(perfil = perfil_logueado)
        departamentos = T_gestor_depa.objects.filter(gestor=gestor).values_list('depa__nom_departa', flat=True)
        fichas = fichas.filter(insti__muni__nom_departa__nom_departa__in=departamentos)


    if estados:
        fichas = fichas.filter(esta__in = estados)
    if instructores:
        incluir_null = 'Sin asignar' in instructores
        nombres_validos = [i for i in instructores if i != 'Sin asignar']

        if incluir_null and nombres_validos:
            fichas = fichas.filter(
                Q(instru__perfil__nom__in = nombres_validos) |
                Q(instru__isnull=True)
                )
        elif incluir_null:
            fichas = fichas.filter(instru__isnull=True)
        else:
            fichas = fichas.filter(instru__perfil__nom__in = nombres_validos)

    if programas:
        fichas = fichas.filter(progra__nom__in = programas)

    data = [
        {
            'id': f.id,
            'num': f.num,
            'grupo': f.grupo.id,
            'estado': f.esta,
            'fecha_aper': f.fecha_aper.strftime('%d/%m/%Y') if f.fecha_aper else None,
            'fecha_cierre': f.fecha_cierre.strftime('%d/%m/%Y') if f.fecha_cierre else None,
            'centro': f.centro.nom,
            'institucion': f.insti.nom,
            'instru': f.instru.perfil.nom if f.instru else None,
            'matricu': f.num_apre_proce,
            'progra': f.progra.nom
        } for f in fichas
    ]
    return JsonResponse(data, safe=False)

@require_POST
@login_required
def cambiar_numero_ficha(request, ficha_id):
    nuevo_num = request.POST.get('nuevo_num', '').strip()

    # Validación básica: campo vacío
    if not nuevo_num:
        return JsonResponse({'status': 'error', 'message': 'Número de ficha inválido.'}, status=400)

    # Validación: solo números
    if not nuevo_num.isdigit():
        return JsonResponse({'status': 'error', 'message': 'El número de ficha debe contener solo dígitos.'}, status=400)

    # Validación: número duplicado (excluyendo el actual)
    if T_ficha.objects.filter(num=nuevo_num).exclude(id=ficha_id).exists():
        return JsonResponse({'status': 'error', 'message': 'Ya existe una ficha con ese número.'}, status=400)

    ficha = get_object_or_404(T_ficha, id=ficha_id)
    ficha.num = nuevo_num
    ficha.save()

    return JsonResponse({'status': 'success', 'message': 'Número de ficha actualizado correctamente.'}, status=200)

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

@login_required
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

@login_required
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

@login_required
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
            'horas_auto': actividad.horas_auto,
            'horas_dire': actividad.horas_dire,
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

@login_required
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

@login_required
def descargar_portafolio_zip(request, ficha_id):
    nodos = T_DocumentFolder.objects.filter(ficha_id=ficha_id).select_related("documento")

    # Creamos un diccionario para construir la jerarquía de carpetas
    folder_map = {}

    for nodo in nodos:
        folder_map[nodo.id] = {
            "id": nodo.id,
            "name": nodo.name,
            "parent_id": nodo.parent_id,
            "tipo": nodo.tipo,
            "documento": nodo.documento if nodo.tipo == "documento" else None,
            "children": []
        }

    # Construimos la jerarquía
    root_nodes = []
    for nodo in folder_map.values():
        if nodo["parent_id"]:
            parent = folder_map.get(nodo["parent_id"])
            if parent:
                parent["children"].append(nodo)
        else:
            root_nodes.append(nodo)

    def agregar_a_zip(zip_file, nodo, ruta_actual):
        nombre = nodo["name"]
        ruta = os.path.join(ruta_actual, nombre)

        if nodo["tipo"] == "carpeta":
            # Creamos una carpeta vacía en el zip
            zip_file.writestr(f"{ruta}/", "")
            for hijo in nodo["children"]:
                agregar_a_zip(zip_file, hijo, ruta)
        elif nodo["tipo"] == "documento" and nodo["documento"] and nodo["documento"].archi:
            path_archivo = nodo["documento"].archi.path
            try:
                with open(path_archivo, "rb") as f:
                    contenido = f.read()
                    zip_file.writestr(f"{ruta}", contenido)
            except FileNotFoundError:
                pass
    # Creamos el zip en memoria
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for nodo in root_nodes:
            agregar_a_zip(zip_file, nodo, "")

    buffer.seek(0)

    response = HttpResponse(buffer, content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename=portafolio_ficha_{ficha_id}.zip'
    return response

@login_required
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

@login_required
def eliminar_documento_portafolio_ficha(request, documento_id):
    if request.method != "DELETE":
        return JsonResponse({"status": "error", "error": "Método no permitido"}, status=405)

    documento = get_object_or_404(T_DocumentFolder, id=documento_id)

    # Si hay un archivo relacionado, eliminarlo manualmente
    if documento.documento and documento.documento.archi:
        archivo_a_eliminar = documento.documento.archi.name
        if archivo_a_eliminar:
            default_storage.delete(archivo_a_eliminar)
        documento.documento.delete()

    documento.delete()

    return JsonResponse({"status": "success", "message": "Eliminado correctamente"}, status=200)


@login_required
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

@login_required
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

@login_required
def descargar_portafolio_aprendiz_zip(request, aprendiz_id):
    # Obtener todos los nodos del árbol
    nodos = T_DocumentFolderAprendiz.objects.filter(aprendiz_id=aprendiz_id).select_related('documento')

    folder_map = {}
    doc_map = {}

    for nodo in nodos:
        folder_map[nodo.id] = {
            "id": nodo.id,
            "name": nodo.name,
            "parent_id": nodo.parent_id,
            "tipo": nodo.tipo,
            "children": [],
        }
        if nodo.tipo == "documento" and nodo.documento:
            doc_map[nodo.id] = nodo.documento

    # Construir jerarquía de carpetas
    root_nodes = []
    for nodo in folder_map.values():
        parent_id = nodo["parent_id"]
        if parent_id:
            folder_map[parent_id]["children"].append(nodo)
        else:
            root_nodes.append(nodo)

    # Función recursiva para añadir al ZIP
    def agregar_a_zip(zip_file, nodo, ruta):
        ruta_actual = os.path.join(ruta, nodo["name"])
        if nodo["tipo"] == "carpeta":
            for hijo in nodo["children"]:
                agregar_a_zip(zip_file, hijo, ruta_actual)
        elif nodo["tipo"] == "documento" and nodo["id"] in doc_map:
            doc = doc_map[nodo["id"]]
            if doc.archi and os.path.isfile(doc.archi.path):
                with open(doc.archi.path, 'rb') as f:
                    file_data = f.read()
                nombre_archivo = f"{doc.nom or os.path.basename(doc.archi.name)}"
                zip_file.writestr(os.path.join(ruta, nombre_archivo), file_data)

    # Crear archivo ZIP en memoria
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for nodo in root_nodes:
            agregar_a_zip(zip_file, nodo, "")

    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename=portafolio_aprendiz_{aprendiz_id}.zip'
    return response

@login_required
def descargar_portafolios_ficha_zip(request, ficha_id):
    # Obtener todos los aprendices de la ficha
    aprendices = T_apre.objects.filter(ficha_id=ficha_id)

    # Crear archivo ZIP en memoria
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for aprendiz in aprendices:
            nodos = T_DocumentFolderAprendiz.objects.filter(aprendiz=aprendiz).select_related('documento')

            folder_map = {}
            doc_map = {}

            for nodo in nodos:
                folder_map[nodo.id] = {
                    "id": nodo.id,
                    "name": nodo.name,
                    "parent_id": nodo.parent_id,
                    "tipo": nodo.tipo,
                    "children": [],
                }
                if nodo.tipo == "documento" and nodo.documento:
                    doc_map[nodo.id] = nodo.documento

            # Construir jerarquía
            root_nodes = []
            for nodo in folder_map.values():
                if nodo["parent_id"]:
                    folder_map[nodo["parent_id"]]["children"].append(nodo)
                else:
                    root_nodes.append(nodo)

            # Función recursiva para añadir al ZIP
            def agregar_a_zip(zip_file, nodo, ruta):
                if nodo["tipo"] == "carpeta":
                    ruta_actual = os.path.join(ruta, nodo["name"])
                    for hijo in nodo["children"]:
                        agregar_a_zip(zip_file, hijo, ruta_actual)
                elif nodo["tipo"] == "documento" and nodo["id"] in doc_map:
                    doc = doc_map[nodo["id"]]
                    if doc.archi and os.path.isfile(doc.archi.path):
                        with open(doc.archi.path, 'rb') as f:
                            file_data = f.read()
                        nombre_archivo = f"{doc.nom or os.path.basename(doc.archi.name)}"
                        # Guardar directamente en la ruta del aprendiz, sin subcarpeta adicional
                        zip_file.writestr(os.path.join(ruta, nombre_archivo), file_data)


            # Carpeta por aprendiz
            carpeta_aprendiz = f"{aprendiz.perfil.dni}_{aprendiz.perfil.nom}_{aprendiz.perfil.apelli}".replace(' ', '_')
            for nodo in root_nodes:
                agregar_a_zip(zip_file, nodo, carpeta_aprendiz)

    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename=portafolios_ficha_{ficha_id}.zip'
    return response


@login_required
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

    if documento.documento and documento.documento.archi:
        archivo_a_eliminar = documento.documento.archi.name
        if archivo_a_eliminar:
            default_storage.delete(archivo_a_eliminar)
        documento.documento.delete()

    documento.delete()

    return JsonResponse({"status": "success", "message": "Eliminado correctamente"}, status=200)


@login_required
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

@login_required
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

@require_GET
@login_required
def obtener_encuentro(request, encuentro_id):
    encuentro = T_encu.objects.get(pk=encuentro_id)

    if not encuentro:
        return JsonResponse({'status': 'error', 'message': 'Encuentro no encontrado'}, status=404)
    
    ausentes_qs = T_encu_apre.objects.filter(encu=encuentro, prese="No")
    ausentes_ids = list(ausentes_qs.values_list('apre_id', flat=True))
    data = {
        'tema': encuentro.tema,
        'lugar': encuentro.lugar,
        'fecha': encuentro.fecha.strftime('%Y-%m-%d'),
        'ausentes': ausentes_ids
    }
    return JsonResponse(data, safe=False)

@require_POST
@login_required
def editar_encuentro(request, encuentro_id):
    try:
        encuentro = T_encu.objects.get(pk=encuentro_id)
    except T_encu.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Encuentro no encontrado'}, status=404)

    tema = request.POST.get('tema')
    lugar = request.POST.get('lugar')
    fecha_str = request.POST.get('fecha')

    try:
        fecha_naive = datetime.strptime(fecha_str, "%Y-%m-%d")
        fecha_aware = timezone.make_aware(fecha_naive)
    except (ValueError, TypeError):
        return JsonResponse({'status': 'error', 'message': 'Formato de fecha inválido'}, status=400)

    # Asignar todos los campos antes de guardar
    encuentro.tema = tema
    encuentro.lugar = lugar
    encuentro.fecha = fecha_aware
    encuentro.save()

    ausentes = request.POST.getlist('aprendices')

    registros = T_encu_apre.objects.filter(encu=encuentro)
    for reg in registros:
        reg.prese = "No" if str(reg.apre.id) in ausentes else "Si"
        reg.save()

    return JsonResponse({'status': 'success', 'message': 'Encuentro actualizado correctamente'}, status=200)


@login_required
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

@login_required
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

@require_POST
@login_required
def editar_actividad(request, actividad_id):


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

###############################################################################################################
#        VISTAS FICHA MASIVO
###############################################################################################################

def formatear_error_csv(fila, errores_campos):
    fila_str = '\n  '.join([f"{k}: '{v}'" for k, v in fila.items()])
    return (
        "⚠️ Error de validación en una fila del archivo:\n"
        "----------------------------------------\n"
        f"Datos de la fila:\n  {fila_str}\n\n"
        f"Errores encontrados:\n" + '\n'.join(errores_campos) + "\n"
        "----------------------------------------"
    )

# Función para generar contraseña aleatoria
def generar_contraseña(length=8):
    caracteres = string.ascii_letters + string.digits
    return ''.join(random.choice(caracteres) for _ in range(length))

@login_required
def cargar_fichas_masivo(request):
    return render(request, 'fichas_masivo_crear.html')

def formatear_error_csv(fila, errores_campos):
    fila_str = '\n  '.join([f"{k}: '{v}'" for k, v in fila.items()])
    return (
        "⚠️ Error de validación en una fila del archivo:\n"
        "----------------------------------------\n"
        f"Datos de la fila:\n  {fila_str}\n\n"
        f"Errores encontrados:\n" + '\n'.join(errores_campos) + "\n"
        "----------------------------------------"
    )


@login_required
@require_POST
def cargar_fichas(request):
    errores = []
    resumen = {
        "insertados": 0,
        "errores": 0,
        "duplicados_dni": []
    }

    archivo = request.FILES.get('archivo')
    if not archivo:
        return JsonResponse({
            "success": False,
            "message": "No se recibió ningún archivo.",
            "errores": ["No se recibió ningún archivo."]
        }, status=400)

    if not archivo.name.lower().endswith('.csv'):
        return JsonResponse({
            "success": False,
            "message": "Solo se permiten archivos CSV (.csv)",
            "errores": ["Solo se permiten archivos CSV (.csv)"]
        }, status=400)

    allowed_mime_types = ['text/csv', 'application/csv', 'text/plain']
    if archivo.content_type not in allowed_mime_types:
        return JsonResponse({
            "success": False,
            "message": "Tipo de archivo no válido (solo CSV)",
            "errores": ["Tipo de archivo no válido (solo CSV)"]
        }, status=400)

    datos_csv = TextIOWrapper(archivo.file, encoding='utf-8-sig')
    contenido_csv = datos_csv.read().replace(';', ',')
    lector = list(csv.DictReader(contenido_csv.splitlines()))
    
    if len(lector) > 60:
        return JsonResponse({
            "success": False,
            "message": "El archivo contiene más de 60 registros.",
            "errores": ["El archivo no debe exceder los 60 registros."]
        }, status=400)
    
    try:
        with transaction.atomic():
            aprendices_creados = []

            for fila in lector:
                try:
                    campos_requeridos = [
                        'email', 'nom', 'apelli', 'tipo_dni', 'dni', 'tele',
                        'dire', 'gene', 'fecha_naci', 'nom_repre', 'dni_repre',
                        'tele_repre', 'dire_repre', 'mail_repre', 'parentezco'
                    ]
                    errores_fila = []

                    for campo in campos_requeridos:
                        if campo not in fila or not fila[campo].strip():
                            errores_fila.append(f"Campo requerido faltante: '{campo}'")

                    dni = fila['dni']
                    if T_perfil.objects.filter(dni=dni).exists():
                        resumen["duplicados_dni"].append(dni)
                        errores_fila.append(f"DNI duplicado en el sistema: {dni}")

                    try:
                        validate_email(fila['email'])
                    except ValidationError:
                        errores_fila.append(f"Email inválido: {fila['email']}")

                    if T_perfil.objects.filter(mail=fila['email']).exists():
                        errores_fila.append(f"Email ya registrado: {fila['email']}")

                    try:
                        fecha_naci = datetime.strptime(fila['fecha_naci'].strip(), '%d/%m/%Y').date()
                    except ValueError:
                        errores_fila.append(f"Fecha de nacimiento inválida: {fila['fecha_naci']}")

                    if errores_fila:
                        error_msg = formatear_error_csv(fila, errores_fila)
                        raise ValidationError(error_msg)

                    base_username = (fila['nom'][:3] + fila['apelli'][:3]).lower()
                    username = base_username
                    i = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{base_username}{i}"
                        i += 1

                    # contraseña = generar_contraseña()
                    user = User.objects.create_user(
                        username=username,
                        password=str(dni),
                        email=fila['email']
                    )

                    perfil = T_perfil.objects.create(
                        user=user,
                        nom=fila['nom'],
                        apelli=fila['apelli'],
                        tipo_dni=fila['tipo_dni'],
                        dni=dni,
                        tele=fila['tele'],
                        dire=fila['dire'],
                        gene=fila['gene'],
                        mail=fila['email'],
                        fecha_naci=fecha_naci,
                        rol="aprendiz"
                    )
                    perfil.full_clean()

                    validate_email(fila['mail_repre'].strip())

                    representante_legal = T_repre_legal.objects.filter(
                        dni=fila['dni_repre']
                    ).first()

                    if not representante_legal:
                        representante_legal = T_repre_legal(
                            nom=fila['nom_repre'],
                            dni=fila['dni_repre'],
                            tele=fila['tele_repre'],
                            dire=fila['dire_repre'],
                            mail=fila['mail_repre'],
                            paren=fila['parentezco']
                        )
                        representante_legal.full_clean()
                        representante_legal.save()

                    aprendiz = T_apre.objects.create(
                        cod="z",
                        esta="activo",
                        perfil=perfil,
                        repre_legal=representante_legal,
                        usu_crea=request.user
                    )
                    aprendiz.full_clean()
                    aprendices_creados.append(aprendiz)
                    resumen["insertados"] += 1

                except Exception as fila_error:
                    raise ValidationError(str(fila_error))

            # Crear ficha y grupo
            cod_ficha = request.POST.get('num_ficha', '').strip()
            fase = request.POST.get('fase_actual')
            colegio = request.POST.get('colegio')
            centro_forma = request.POST.get('centro_forma')
            programa = request.POST.get('programa')


            if not fase or not colegio or not centro_forma or not programa:
                raise ValidationError("Faltan datos para crear la ficha.")

            try:
                programaf = T_progra.objects.get(id=programa)
            except T_progra.DoesNotExist:
                raise ValidationError("Programa de formación no encontrado.")

            if cod_ficha and T_ficha.objects.filter(num=cod_ficha).exists():
                raise ValidationError("Numero de ficha ya existe.")

            centro = T_centro_forma.objects.filter(pk = centro_forma).first()
            institucion = T_insti_edu.objects.filter(pk = colegio).first()
            grupo = T_grupo.objects.create(
                esta= 'Masivo',
                fecha_crea= timezone.now(),
                autor=request.user,
                num_apre_poten = len(aprendices_creados),
                centro = centro,
                insti = institucion,
                progra = programaf
            )
            grupo.full_clean()
            grupo.save()

            departamento = institucion.muni.nom_departa if institucion and institucion.muni else None

            gestor_depa = T_gestor_depa.objects.filter(depa=departamento).select_related('gestor').first()

            if not gestor_depa:
                gestor = T_gestor.objects.get(pk=1)
            else:
                gestor = gestor_depa.gestor

            T_gestor_grupo.objects.create(
                fecha_crea=timezone.now(),
                autor=request.user,
                gestor=gestor,
                grupo=grupo
            )
            
            documentos_matricula = [
                'Documento de Identidad del aprendiz',
                'Registro civil',
                'Certificado de Afiliación de salud',
                'Formato de Tratamiento de Datos del Menor de Edad',
                'Compromiso del Aprendiz',
            ]

            perfili = T_perfil.objects.get(user = request.user)
            instructor = T_instru.objects.get(perfil = perfili)

            ficha = T_ficha.objects.create(
                num=cod_ficha,
                grupo=grupo,
                fecha_aper=timezone.now(),
                fecha_cierre=None,
                insti=institucion,
                centro=centro,
                progra=programaf,
                num_apre_proce=len(aprendices_creados),
                num_apre_forma=0,
                num_apre_pendi_regi=len(aprendices_creados),
                esta="Activo",
                instru = instructor
            )

            for aprendiz in aprendices_creados:
                aprendiz.grupo = grupo
                aprendiz.ficha = ficha
                aprendiz.esta_docu = "Pendiente"
                aprendiz.save()

                for documento in documentos_matricula:
                    T_prematri_docu.objects.create(
                        nom=documento,
                        apren=aprendiz,
                        esta="Pendiente",
                        vali="0"
                    )


            for f in range(1, int(fase)):
                T_fase_ficha.objects.create(
                    fase_id=f,
                    ficha=ficha,
                    fecha_ini=timezone.now(),
                    instru=instructor,
                    vige=0
                )

            T_fase_ficha.objects.create(
                fase_id = fase,
                ficha = ficha,
                fecha_ini = timezone.now(),
                instru = instructor,
                vige  = 1
            )

            compe_ids = T_compe_progra.objects.filter(progra=ficha.progra).values('compe_id')
            raps = T_raps.objects.filter(compe__in=Subquery(compe_ids))

            raps_ficha_objs = []

            for rap in raps:
                for fase in rap.compe.fase.all():
                    raps_ficha_objs.append(
                        T_raps_ficha(ficha=ficha, rap=rap, fase=fase)
                    )

            T_raps_ficha.objects.bulk_create(raps_ficha_objs)

            crear_datos_prueba(ficha.id)

            for aprendiz in aprendices_creados:
                crear_datos_prueba_aprendiz(aprendiz.id)

    except ValidationError as e:
        return JsonResponse({
            "success": False,
            "message": "Se detectaron errores, operación revertida.",
            "errores": e.messages,
            "resumen": resumen
        }, status=400)

    return JsonResponse({
        "success": True,
        "message": (
            f"✅ Ficha y aprendices creados correctamente.\n\n"
            f"Ficha creada: ID: {ficha.id}, Numero: {ficha.num or 'Sin numero'}\n"
            f"Grupo creado:\n  ID: {grupo.id}"
            f"\nAprendices insertados: {resumen['insertados']}\n"
            f"{'DNIs duplicados encontrados: ' + ', '.join(resumen['duplicados_dni']) if resumen['duplicados_dni'] else ''}"
        ),
        "resumen": resumen,
        "errores": errores
    }, status=201)


@require_GET
@login_required
def obtener_opciones_fichas_masivo_departamentos(request):
    departamentos = T_departa.objects.all().distinct().values('id', 'nom_departa')
    data = [{'id': d['id'], 'nom': d['nom_departa']} for d in departamentos]
    return JsonResponse(list(data), safe=False)

@require_GET
@login_required
def obtener_opciones_fichas_masivo_municipios(request):
    departamento_id = request.GET.get('departamento')

    queryset = T_munici.objects.all()

    if departamento_id:
        queryset = queryset.filter(nom_departa_id=departamento_id)

    municipios = queryset.distinct().values('id', 'nom_munici')
    data = [{'id': m['id'], 'nom': m['nom_munici']} for m in municipios]
    return JsonResponse(list(data), safe=False)

@require_GET
@login_required
def obtener_opciones_fichas_masivo_colegios(request):
    municipio_id = request.GET.get('municipio')

    queryset = T_insti_edu.objects.all()

    if municipio_id:
        queryset = queryset.filter(muni_id=municipio_id)
    else:
        queryset = T_insti_edu.objects.none()

    instituciones = queryset.distinct().values('id', 'nom')
    data = [{'id': i['id'], 'nom': i['nom']} for i in instituciones]
    return JsonResponse(list(data), safe=False)

@require_GET
@login_required
def obtener_opciones_fichas_masivo_centros(request):
    centros = T_centro_forma.objects.all().distinct().values('id', 'nom')
    data = [{'id': c['id'], 'nom': c['nom']} for c in centros]
    return JsonResponse(list(data), safe=False)

@require_GET
@login_required
def obtener_opciones_fichas_masivo_programas(request):
    programas = T_progra.objects.all().distinct().values('id', 'nom')
    data = [{'id': p['id'], 'nom': p['nom']} for p in programas]
    return JsonResponse(list(data), safe=False)

###############################################################################################################
#        VISTAS APRENDIZ
###############################################################################################################

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

###############################################################################################################
#        VISTAS PROGRAMA
###############################################################################################################

@login_required
def listar_programas(request):
    programas = T_progra.objects.all()
    return render(request, 'programas.html', {'programas': programas})

@login_required
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

@login_required
def competencias(request):
    competencia_form = CompetenciaForm()
    return render(request, 'competencias.html', {
        'competencia_form': competencia_form
        })

@login_required
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

require_GET
@login_required
def filtrar_competencias(request):
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

@login_required
def obtener_opciones_fases(request):
    fases = T_fase.objects.filter(t_compe_fase__isnull=False).distinct().values_list('nom')
    return JsonResponse(list(fases), safe=False)

@login_required
def obtener_opciones_programas(request):
    programas = T_progra.objects.filter(t_compe_progra__isnull=False).distinct().values_list('nom')
    return JsonResponse(list(programas), safe=False)

@login_required
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

@login_required
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

@login_required
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

@login_required
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

@login_required
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

@login_required
def obtener_opciones_fases_raps(request):
    fases = T_fase.objects.filter(
        t_compe_fase__compe__t_raps__isnull=False
    ).distinct().values_list('nom', flat=True)

    return JsonResponse(list(fases), safe=False)

@login_required
def obtener_opciones_programas_raps(request):
    programas = T_progra.objects.filter(
        t_compe_progra__compe__t_raps__isnull=False
    ).distinct().values_list('nom', flat=True)

    return JsonResponse(list(programas), safe=False)

@login_required
def obtener_opciones_competencias_raps(request):
    competencias = T_compe.objects.filter(
        t_raps__isnull=False
    ).distinct().values_list('nom', flat=True)

    return JsonResponse(list(competencias), safe=False)

@login_required
def obtener_competencias_programa(request, id_progra):
    competencias = T_compe_progra.objects.filter(progra_id = id_progra).distinct()
    data = list(competencias.values('compe__id', 'compe__nom'))
    return JsonResponse(data, safe=False)

@login_required
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

@login_required
def obtener_opciones_competencias(request):
    competencias = T_compe.objects.all().values('id', 'nom')
    return JsonResponse(list(competencias), safe=False)

@login_required
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

@login_required
def listar_guias(request):
    guia_form = GuiaForm()
    guias = T_guia.objects.all()
    return render(request, 'guias.html', {
        'guias': guias,
        'guia_form': guia_form
        })

@login_required
def crear_guia(request):
    if request.method == 'POST':
        guia_form = GuiaForm(request.POST)
        if guia_form.is_valid():
            guia_form.save()
            return JsonResponse({'status': 'success', 'message': 'Guia creada'}, status = 200)
    return JsonResponse({'status': 'error', 'message': 'Metodo no permitido'}, status = 405)

@require_GET
@login_required
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
@login_required
def editar_guia(request, guia_id):
    guia = T_guia.objects.filter(pk=guia_id).first()
    if not guia:
        return JsonResponse({'status': 'error', 'message': 'Guia no encontrada'}, status=404)
    
    form_guia = GuiaForm(request.POST, instance=guia)

    if form_guia.is_valid():
        form_guia.save()
        return JsonResponse({'status': 'success', 'message': 'Guia actualizada con exito'}, status = 200)
    return JsonResponse({'status': 'error', 'message': 'Error al actualizar la guia', 'errors': form_guia.errors}, status=400)

@login_required
def eliminar_doc(request, documento_id):
    if request.method == "DELETE":
        try:
            documento = T_DocumentFolder.objects.get(id=documento_id)

            # Eliminar archivo físico antes de borrar el modelo relacionado
            if documento.documento and documento.documento.archi:
                archivo_a_eliminar = documento.documento.archi.name
                if archivo_a_eliminar:
                    default_storage.delete(archivo_a_eliminar)
                documento.documento.delete()

            documento.delete()

            return JsonResponse({"success": True, "message": "Documento eliminado exitosamente."}, status=200)

        except T_DocumentFolder.DoesNotExist:
            return JsonResponse({"success": False, "message": "Documento no encontrado."}, status=404)

    return JsonResponse({"success": False, "message": "Método no permitido."}, status=405)



@login_required
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
@login_required
def get_municipios(request, departamento_id):
    municipio_qs = T_munici.objects.filter(nom_departa_id=departamento_id)
    municipios = list(municipio_qs.values('id', 'nom_munici'))
    return JsonResponse(municipios, safe=False)

# Vista para cargar las instituciones según el municipio
@login_required
def get_instituciones(request, municipio_id):
    instituciones_qs = T_insti_edu.objects.filter(muni_id=municipio_id)
    instituciones = list(instituciones_qs.values('id', 'nom'))
    return JsonResponse(instituciones, safe=False)

# Vista para cargar los municipios según el departamento
@login_required
def get_centros(request, departamento_id):
    centro_qs = T_centro_forma.objects.filter(depa_id=departamento_id)
    centros = list(centro_qs.values('id', 'nom'))
    return JsonResponse(centros, safe=False)

@login_required
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

        for aprendiz_id in ids:
            # Por defecto, asumimos que NO aprobó (0)
            nota = '0'

            # Si este aprendiz tiene un checkbox marcado, su valor estará en request.POST.getlist('nota[]')
            # Comprobamos si el input con name="nota[]" y value=aprendiz_id existe
            checkbox_name = f"nota_{aprendiz_id}"
            if checkbox_name in request.POST:
                nota = '1'

            aprendiz = T_apre.objects.get(id=aprendiz_id)

            T_cali.objects.update_or_create(
                apre=aprendiz,
                acti=actividad,
                defaults={'cali': nota}
            )
        return JsonResponse({'status': 'success', 'message': 'Calificado!', 'actividad_id': actividad_id}, status = 200)
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status = 405)

@login_required
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

@login_required
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
        "horas_directas": actividad.horas_dire,
        "horas_autonomas": actividad.horas_auto,
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

@login_required
def detalle_programa(request, programa_id):
    programa = T_progra.objects.get(pk=programa_id)

    competencias = []
    for compe in T_compe.objects.filter(progra=programa):
        fases = T_fase.objects.filter(t_compe_fase__compe=compe).values_list('nom', flat=True)
        competencias.append({
            'nom': compe.nom,
            'fase': list(fases),
        })

    raps = []
    for compe in T_compe.objects.filter(progra=programa):
        for rap in compe.t_raps_set.all():
            raps.append({
                'nom': rap.nom,
                'compe': compe.nom,
            })

    return JsonResponse({
        'cod_prog': programa.cod_prog,
        'nom': programa.nom,
        'nomd': programa.nomd,
        'competencias': competencias,
        'raps': raps,
    })

def link_callback(uri, rel):
    result = finders.find(uri.replace(settings.STATIC_URL, ""))
    if result:
        return result
    raise Exception(f"Media URI must start with {settings.STATIC_URL}")

@login_required
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

        # Estilos
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        fill_header = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
        fill_asistencias_col = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
        fill_fallas_col = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
        fill_fila_asistentes = PatternFill(start_color="A9D08E", end_color="A9D08E", fill_type="solid")
        fill_fila_fallas = PatternFill(start_color="F4B084", end_color="F4B084", fill_type="solid")

        if ficha.instru and ficha.instru.perfil:
            nombre_instructor = f"{ficha.instru.perfil.nom.upper()} {ficha.instru.perfil.apelli.upper()}"
        else:
            nombre_instructor = "INSTRUCTOR NO ASIGNADO"

        # Info general
        ws['A1'] = "1 = Asistencia (Sí)"
        ws['C1'] = f"Ficha: {ficha.num}"
        ws['A2'] = "0 = No asistencia (No)"
        ws['C2'] = f"Programa: {ficha.progra.nom}"
        ws['C3'] = f"Instructor: {nombre_instructor}"
        ws['A5'] = "PLANILLA  DE ASISTENCIA"

        headers = ["No.", "TIPO ID", "NUMERO ID", "APELLIDOS Y NOMBRES", "E-MAIL", "TELEFONO"]
        fechas = list(T_encu.objects.filter(ficha=ficha).order_by('fecha').values_list('id', 'fecha'))
        headers += [fecha.strftime("%d-%b-%y") for _, fecha in fechas]
        headers += ["Asistencias", "Fallas"]

        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=6, column=col, value=header)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
            cell.fill = fill_header
            cell.border = thin_border

        conteo_por_fecha = {encu_id: {'asistencias': 0, 'faltas': 0} for encu_id, _ in fechas}
        aprendices = aprendices.order_by('perfil__apelli', 'perfil__nom')

        for i, apre in enumerate(aprendices, start=1):
            row_num = i + 6
            perfil = apre.perfil
            asistencias = T_encu_apre.objects.filter(apre=apre, encu__ficha=ficha).select_related('encu')
            asistencia_por_id_encu = {
                a.encu_id: 1 if a.prese.strip().lower() == 'si' else 0 for a in asistencias
            }

            data = [
                i,
                perfil.tipo_dni,
                perfil.dni,
                f"{perfil.apelli} {perfil.nom}",
                perfil.mail,
                perfil.tele
            ]
            for col_idx, val in enumerate(data, start=1):
                cell = ws.cell(row=row_num, column=col_idx, value=val)
                cell.border = thin_border

            total_asistencias = 0
            for j, (encu_id, _) in enumerate(fechas, start=1):
                valor = asistencia_por_id_encu.get(encu_id, 0)
                col_idx = 6 + j
                cell = ws.cell(row=row_num, column=col_idx, value=valor)
                cell.alignment = Alignment(horizontal='center')
                cell.border = thin_border
                total_asistencias += valor

                if valor == 1:
                    conteo_por_fecha[encu_id]['asistencias'] += 1
                else:
                    conteo_por_fecha[encu_id]['faltas'] += 1

            total_fallas = len(fechas) - total_asistencias
            asist_cell = ws.cell(row=row_num, column=6 + len(fechas) + 1, value=total_asistencias)
            fallas_cell = ws.cell(row=row_num, column=6 + len(fechas) + 2, value=total_fallas)

            asist_cell.fill = fill_asistencias_col
            fallas_cell.fill = fill_fallas_col
            asist_cell.border = thin_border
            fallas_cell.border = thin_border
            asist_cell.alignment = fallas_cell.alignment = Alignment(horizontal='center')

        fila_totales_asistentes = len(aprendices) + 7
        fila_totales_fallas = len(aprendices) + 8

        ws.cell(row=fila_totales_asistentes, column=6).value = "Asistentes"
        ws.cell(row=fila_totales_fallas, column=6).value = "No asistentes"

        for j, (encu_id, _) in enumerate(fechas, start=1):
            asistentes = conteo_por_fecha[encu_id]['asistencias']
            no_asistentes = conteo_por_fecha[encu_id]['faltas']

            for fila, valor, fill in [
                (fila_totales_asistentes, asistentes, fill_fila_asistentes),
                (fila_totales_fallas, no_asistentes, fill_fila_fallas),
            ]:
                cell = ws.cell(row=fila, column=6 + j, value=valor)
                cell.font = Font(bold=True)
                cell.fill = fill
                cell.alignment = Alignment(horizontal='center')
                cell.border = thin_border

        # Ajustar ancho de columnas
        for col in range(1, len(headers) + 1):
            ws.column_dimensions[get_column_letter(col)].auto_size = True  # o set un ancho fijo si no funciona bien

        # Guardar y retornar
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename=f"Planilla_Asistencia_{ficha.num}.xlsx")

    return HttpResponse("Formato no válido", status=400)

@login_required
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

@login_required
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

@login_required
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