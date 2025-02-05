import json
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.safestring import mark_safe
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseNotAllowed
from dal import autocomplete
from django.views import generic
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from commons.models import T_ficha,T_gestor_depa, T_grupo,T_docu,T_perfil, T_insti_edu,T_insti_docu, T_centro_forma, T_munici, T_gestor_grupo, T_prematri_docu, T_apre,T_gestor, T_gestor_insti_edu
from .forms import AsignarAprendicesGrupoForm, GrupoForm, AsignarAprendicesMasivoForm, AsignarInstiForm
from .scripts.cargar_tree_apre import crear_datos_prueba_aprendiz
from django.core.files.storage import default_storage
from datetime import datetime
from django.contrib import messages
from django.db import transaction
from django.db import models
from django.contrib.auth.models import User
import zipfile
from PyPDF2 import PdfMerger
import io
import os
import csv

@login_required
def grupos_prematricula(request):
    perfil = getattr(request.user, 't_perfil', None)
    rol = perfil.rol
    if perfil.rol == 'gestor':
        gestor = T_gestor.objects.get(perfil=perfil)
        grupos = T_gestor_grupo.objects.filter(gestor=gestor)
    
    if perfil.rol == 'lider':
        grupos = T_gestor_grupo.objects.all()
    
    return render(request, 'grupos_prematricula.html', {
        'grupos': grupos,
        'rol': rol
    })

@login_required
def asignar_aprendices(request, grupo_id=None):
    grupo = None
    if grupo_id:
        grupo = get_object_or_404(T_grupo, id=grupo_id)

    # Formularios
    aprendiz_asi_form = AsignarAprendicesGrupoForm()
    aprendiz_masivo_form = AsignarAprendicesMasivoForm()

    if request.method == 'POST':
        documentos_matricula = [
            'Carta Intención',
            'Documentos Identidad de los aprendices',
            'Formato de Inscripción Especial 2025',
            'Certificado de Afiliación de salud',
            'Compromiso del Aprendiz',
            'Formato de Tratamiento de Datos del Menor de Edad',
            'Certificado de aprobación de Grado Noveno',
            'Acta de Compromiso de Articulación',
            'Registro civil'
        ]

        errores = []
        resumen = {
            "asignados": 0,
            "errores": 0,
            "duplicados": 0,
            "ya_asignados": 0
        }

        # Detección de qué formulario fue enviado
        if 'aprendices' in request.POST:  # Formulario de asignación manual
            aprendiz_asi_form = AsignarAprendicesGrupoForm(request.POST)
            if aprendiz_asi_form.is_valid() and grupo:
                try:
                    with transaction.atomic():
                        grupo.esta = 'Validacion matriculas'
                        grupo.save()

                        aprendices = aprendiz_asi_form.cleaned_data['aprendices']
                        for aprendiz in aprendices:
                            if aprendiz.grupo is not None:
                                errores.append(f"El aprendiz {aprendiz.perfil.nom} {aprendiz.perfil.apelli} ya está asignado al grupo {aprendiz.grupo}.")
                                resumen["ya_asignados"] += 1
                                continue

                            aprendiz.grupo = grupo
                            aprendiz.save()

                            for documento in documentos_matricula:
                                T_prematri_docu.objects.create(
                                    nom=documento,
                                    apren=aprendiz,
                                    esta="Pendiente",
                                    vali="0"
                                )

                            resumen["asignados"] += 1

                    return redirect('pre_matricula')

                except Exception as e:
                    errores.append(f"Error al asignar aprendices: {str(e)}")
                    resumen["errores"] += 1

        elif 'archivo' in request.FILES:  # Formulario de carga masiva
            aprendiz_masivo_form = AsignarAprendicesMasivoForm(request.POST, request.FILES)
            if aprendiz_masivo_form.is_valid():
                archivo = request.FILES['archivo']
                datos_csv = io.TextIOWrapper(archivo.file, encoding='utf-8-sig')

                # Normalizar separadores de columna
                contenido_csv = datos_csv.read().replace(';', ',')
                lector = csv.DictReader(contenido_csv.splitlines())

                # Validar estructura del CSV
                if lector.fieldnames != ['dni']:
                    errores.append("El archivo CSV debe contener solo una columna llamada 'dni'.")
                    resumen["errores"] += 1
                else:
                    try:
                        with transaction.atomic():

                            for fila in lector:
                                dni = fila.get('dni', '').strip()
                                if not dni:
                                    errores.append(f"Fila con DNI vacío: {fila}")
                                    resumen["errores"] += 1
                                    continue

                                try:
                                    perfil = T_perfil.objects.get(dni=dni)
                                    aprendiz = T_apre.objects.get(perfil=perfil)

                                    if aprendiz.grupo is not None:
                                        errores.append(f"El aprendiz {perfil.nom} {perfil.apelli} ya está asignado al grupo {aprendiz.grupo}.")
                                        resumen["ya_asignados"] += 1
                                        continue

                                    aprendiz.grupo = grupo
                                    aprendiz.save()

                                    for documento in documentos_matricula:
                                        T_prematri_docu.objects.create(
                                            nom=documento,
                                            apren=aprendiz,
                                            esta="Pendiente",
                                            vali="0"
                                        )

                                    resumen["asignados"] += 1

                                except T_perfil.DoesNotExist:
                                    errores.append(f"No se encontró un perfil con DNI {dni}. Fila omitida.")
                                    resumen["errores"] += 1
                                except T_apre.DoesNotExist:
                                    errores.append(f"No se encontró un aprendiz asociado al DNI {dni}. Fila omitida.")
                                    resumen["errores"] += 1
                            # Solo cambiar el estado si no hubo errores
                            if not errores:
                                grupo.esta = 'Validacion matriculas'
                                grupo.save()
                    except Exception as e:
                        errores.append(f"Error al procesar la carga masiva: {str(e)}")
                        resumen["errores"] += 1

            else:
                errores.append("El formulario de carga masiva no es válido. Revisa el archivo enviado.")
                resumen["errores"] += 1

        # Renderizar feedback al usuario
        return render(request, 'asignar_aprendices.html', {
            'aprendiz_asi_form': aprendiz_asi_form,
            'aprendiz_masivo_form': aprendiz_masivo_form,
            'grupo': grupo,
            'errores': errores,
            'resumen': resumen
        })

    return render(request, 'asignar_aprendices.html', {
        'aprendiz_asi_form': aprendiz_asi_form,
        'aprendiz_masivo_form': aprendiz_masivo_form,
        'grupo': grupo,
    })



@login_required
def confirmar_documentacion(request, grupo_id):
    grupo = T_grupo.objects.get(id=grupo_id)
    grupo.esta = 'En radicacion'
    grupo.save()
    return redirect('pre_matricula')

@login_required
def ver_docs_prematricula_grupo(request, grupo_id):
    grupo = get_object_or_404(T_grupo, id=grupo_id)
    perfil = getattr(request.user, 't_perfil', None)
    rol = perfil.rol

    # Obtener los aprendices de la ficha
    aprendices = T_apre.objects.filter(grupo=grupo)
    
    # Obtener documentos por aprendiz
    documentos_por_aprendiz = {}
    for aprendiz in aprendices:
        documentos = T_prematri_docu.objects.filter(apren=aprendiz)
        documentos_por_aprendiz[aprendiz] = documentos

    # Obtener documentos de la institución asociada al grupo
    institucion = grupo.insti  # Asumiendo que 'insti' es la relación con la institución
    documentos_institucion = T_insti_docu.objects.filter(insti=institucion)

    return render(request, 'detalle_docs_prematricula.html', {
        'grupo': grupo,
        'documentos_por_aprendiz': documentos_por_aprendiz,
        'documentos_institucion': documentos_institucion,  # Documentos de la institución
        'rol': rol
    })

@login_required
def descargar_documentos_grupo(request, grupo_id, documento_tipo):
    # Obtener el grupo
    grupo = get_object_or_404(T_grupo, id=grupo_id)

    # Obtener los aprendices del grupo
    aprendices = T_apre.objects.filter(grupo=grupo)

    # Crear un objeto para combinar PDFs
    merger = PdfMerger()

    # Recorrer cada aprendiz y buscar el documento específico asociado
    for aprendiz in aprendices:
        try:
            # Obtener el documento del tipo especificado para el aprendiz
            documento_relacionado = T_prematri_docu.objects.filter(
                apren=aprendiz,
                nom=documento_tipo,  # Filtrar por el tipo de documento
                docu__esta='Activo'         # Solo considerar documentos activos
            ).first()

            # Si el documento existe, agregarlo al PDF combinado
            if documento_relacionado and documento_relacionado.docu and documento_relacionado.docu.archi:
                file_path = documento_relacionado.docu.archi.path  # Ruta completa del archivo
                merger.append(file_path)
        except Exception as e:
            print(f"Error con el aprendiz {aprendiz.id}: {e}")

    # Verificar si se agregaron documentos al merger
    if not merger.pages:
        messages.error(request, f"No hay documentos para combinar.")
        return redirect(request.META.get('HTTP_REFERER', '/')) 

    # Crear una respuesta HTTP para enviar el PDF combinado
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="documentos_{grupo.id}_{documento_tipo}.pdf"'

    # Escribir el contenido combinado en la respuesta
    merger.write(response)
    merger.close()

    return response


def descargar_documentos_zip(request, aprendiz_id):
    # Obtén todos los documentos del estudiante
    aprendiz = get_object_or_404(T_apre, id=aprendiz_id)
    documentos = T_prematri_docu.objects.filter(apren=aprendiz)

    # Crea un archivo ZIP en memoria
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for documento in documentos:
            if documento.docu and documento.docu.archi:
                # Obtén el archivo del documento
                archivo = documento.docu.archi
                # Obtén el nombre original del archivo
                nombre_original = os.path.basename(archivo.name)  # Elimina la ruta de la carpeta

                # Escribe el archivo en el ZIP
                with archivo.open('rb') as f:
                    zip_file.writestr(nombre_original, f.read())

    # Prepara la respuesta para enviar el archivo ZIP
    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="documentos_{aprendiz.perfil.nom}_{aprendiz.perfil.apelli}.zip"'
    
    return response

def confirmar_documento(request, documento_id, grupo_id):
    grupo = T_grupo.objects.get(id=grupo_id)
    documento = T_prematri_docu.objects.get(id=documento_id)    
    documento.vali = "1"
    documento.usr_apro = request.user
    documento.fecha_apro = datetime.now()
    documento.save()
    return redirect(request.META.get('HTTP_REFERER', '/'))

def confirmar_documento_insti(request, documento_id, institucion_id):
    institucion = T_insti_edu.objects.get(id=institucion_id)
    documento = T_insti_docu.objects.get(id=documento_id)    
    documento.vali = "1"
    documento.usr_apro = request.user
    documento.fecha_apro = datetime.now()
    documento.save()
    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def instituciones_gestor(request):
    # Obtén el perfil del usuario autenticado
    perfil = getattr(request.user, 't_perfil', None)
        # Filtra las instituciones asignadas al gestor actual
    if perfil.rol == 'gestor':  # Formulario de asignación manual
        gestor = T_gestor.objects.get(perfil = perfil)
        instituciones = T_gestor_insti_edu.objects.filter(gestor=gestor)
        print(instituciones)
    if perfil.rol == 'lider':
        instituciones = T_gestor_insti_edu.objects.all()
    total_instituciones = T_insti_edu.objects.count()
    instituciones_asignadas = T_gestor_insti_edu.objects.filter(esta='activo').values('insti').distinct().count()
    instituciones_con_grupos = T_grupo.objects.values('insti').distinct().count()
    instituciones_sin_zona = T_insti_edu.objects.filter(zona__isnull=True).count()
    instituciones_con_multiples_grupos = (
        T_grupo.objects.values('insti')
        .annotate(grupo_count=models.Count('id'))
        .filter(grupo_count__gt=1)
        .count()
    )
    return render(request, 'instituciones_gestor.html', {
        'total_instituciones': total_instituciones,
        'instituciones_asignadas': instituciones_asignadas,
        'instituciones_con_grupos': instituciones_con_grupos,
        'instituciones_sin_zona': instituciones_sin_zona,
        'instituciones_con_multiples_grupos': instituciones_con_multiples_grupos,
        'instituciones': instituciones,
    })

# Enviar datos a los filtros de institucion:

def obtener_opciones_municipios(request):
    perfil = T_perfil.objects.get(user=request.user)
    if perfil.rol == 'gestor':
        gestor = T_gestor.objects.get(perfil=perfil)
        municipios_gest = T_gestor_insti_edu.objects.filter(gestor=gestor).values_list('insti__muni__nom_munici', flat=True).distinct()
        print(municipios_gest)
        municipios = T_munici.objects.filter(nom_munici__in=municipios_gest).values_list('nom_munici', flat=True).distinct()
    if perfil.rol == 'lider':
        municipios_gest = T_gestor_insti_edu.objects.all().values_list('insti__muni__nom_munici', flat=True).distinct()
        municipios = T_munici.objects.filter(nom_munici__in=municipios_gest).values_list('nom_munici', flat=True).distinct()
    return JsonResponse(list(municipios), safe=False)

def obtener_opciones_estados(request):
    estados = T_insti_edu.objects.values_list('esta', flat=True).distinct()
    return JsonResponse(list(estados), safe=False)

def obtener_opciones_sectores(request):
    sectores = T_insti_edu.objects.values_list('secto', flat=True).distinct()
    return JsonResponse(list(sectores), safe=False)

# Listado filtrado

def filtrar_instituciones(request):
    municipio = request.GET.getlist('municipio', [])
    estado = request.GET.getlist('estado', [])
    sector = request.GET.getlist('sector', [])

    # Obtén el perfil del usuario autenticado
    perfil = getattr(request.user, 't_perfil', None)
        # Filtra las instituciones asignadas al gestor actual
    if perfil.rol == 'gestor':  # Formulario de asignación manual
        gestor = T_gestor.objects.get(perfil = perfil)
        instituciones = T_gestor_insti_edu.objects.filter(gestor=gestor)
        print(instituciones)
    if perfil.rol == 'lider':
        instituciones = T_gestor_insti_edu.objects.all()

    if municipio:
        instituciones = instituciones.filter(insti__muni__nom_munici__in=municipio)
    if estado:
        instituciones = instituciones.filter(insti__esta__in=estado)
    if sector:
        instituciones = instituciones.filter(insti__secto__in=sector)

    resultados = [
        {
            'id': i.id,
            'nombre': i.insti.nom,
            'direccion': i.insti.dire,
            'municipio': i.insti.muni.nom_munici,
            'departamento': i.insti.muni.nom_departa.nom_departa,
            'sector': i.insti.secto,
            'estado': i.insti.esta,
            'dane': i.insti.dane,
            'genero': i.insti.gene,
            'zona': i.insti.zona,
            'estado_docu': i.insti.esta_docu,
            'detalle_url': reverse('instituciones_docs', args=[i.insti.id])  # Genera la URL
        }
        for i in instituciones
    ]
    return JsonResponse(resultados, safe=False)

def eliminar_institucion_gestor(request, id):
    if request.method == 'DELETE':
        try:
            institucion_gest = T_gestor_insti_edu.objects.get(id=id)
            id_institucion = institucion_gest.insti.id

            # Verificar si hay registros en T_grupo relacionados con la institución
            grupos_asociados = T_grupo.objects.filter(insti_id=id_institucion).exists()

            if grupos_asociados:
                return JsonResponse({
                    'error': 'No se puede eliminar la institución porque tiene grupos asociados.'
                }, status=400)

            # Eliminar documentos asociados en T_insti_docu
            T_insti_docu.objects.filter(insti_id=id_institucion).delete()

            # Eliminar la institución gestora
            institucion_gest.delete()

            return JsonResponse({'mensaje': 'Institución y documentos asociados eliminados correctamente.'}, status=200)

        except T_gestor_insti_edu.DoesNotExist:
            return JsonResponse({'error': 'Institución no encontrada.'}, status=404)
    else:
        return HttpResponseNotAllowed(['DELETE'])

def cargar_documento_prematricula(request, documento_id, aprendiz_id, grupo_id):

    # Configuración de restricciones
    TAMANO_MAXIMO = 3 * 1024 * 1024  # 3 MB
    TIPOS_PERMITIDOS = ['pdf']  # Extensiones permitidas
    
    documento = T_prematri_docu.objects.filter(id=documento_id, apren=aprendiz_id).first()
    grupo = T_grupo.objects.get(id=grupo_id)
    if not documento:
        # Redirige si el documento no pertenece al aprendiz logueado
        return render(request, 'grupos_prematricula.html', {
        'grupo': grupo
    })

    if request.method == 'POST' and 'archivo' in request.FILES:
        archivo = request.FILES['archivo']

        extension = archivo.name.split('.')[-1].lower()
        
        # Validar el tipo de archivo
        if extension not in TIPOS_PERMITIDOS:
            messages.error(request, f"Tipo de archivo no permitido. Los tipos permitidos son: {', '.join(TIPOS_PERMITIDOS)}.")
            return redirect('ver_docs_prematricula', grupo_id= grupo.id)
        
        # Validar el tamaño del archivo
        if archivo.size > TAMANO_MAXIMO:
            messages.error(request, f"El archivo excede el tamaño máximo permitido de {TAMANO_MAXIMO // (1024 * 1024)} MB.")
            return redirect('ver_docs_prematricula', grupo_id= grupo.id)

        ruta = f'documentos/aprendices/prematricula/{documento.apren.perfil.nom}{documento.apren.perfil.apelli}{documento.apren.perfil.dni}/{archivo.name}'

        ruta_guardada = default_storage.save(ruta, archivo)

        # Crear un registro en T_docu
        t_docu = T_docu.objects.create(
            nom=archivo.name,
            tipo= archivo.name.split('.')[-1],
            tama=f"{archivo.size // 1024} KB",
            archi=ruta_guardada,
            priva='No',
            esta='Activo'
        )

        documento.esta = "Cargado"
        documento.docu = t_docu
        documento.fecha_carga = datetime.now()
        documento.usr_carga = request.user
        documento.save()
        messages.success(request, "Documento cargado exitosamente.")
        return redirect('ver_docs_prematricula', grupo_id= grupo.id)

    return render(request, 'detalle_docs_prematricula.html', {
        'grupo': grupo
        })

@login_required  # Funcion para eliminar documento de prematricula aprendiz
def eliminar_documento_pre(request, documento_id):
    documentot = get_object_or_404(T_docu, id = documento_id)
    prematri_docu = T_prematri_docu.objects.filter(docu_id=documentot.id).first()
    prematri_docu.esta = 'Pendiente'
    prematri_docu.vali = '0'
    prematri_docu.save()
    documentot.delete()
    return redirect(request.META.get('HTTP_REFERER', '/'))

def descargar_documentos_grupo_zip(request, grupo_id):
    # Obtén el grupo por su ID
    grupo = get_object_or_404(T_grupo, id=grupo_id)
    # Obtén todos los aprendices del grupo
    aprendices = T_apre.objects.filter(grupo=grupo_id)

    # Crea un archivo ZIP en memoria
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for aprendiz in aprendices:
            # Obtén los documentos del aprendiz
            documentos = T_prematri_docu.objects.filter(apren=aprendiz)

            # Crea una carpeta dentro del ZIP con el nombre del aprendiz
            carpeta_aprendiz = f"{aprendiz.perfil.nom}_{aprendiz.perfil.apelli}/"
            for documento in documentos:
                if documento.docu and documento.docu.archi:
                    # Obtén el archivo del documento
                    archivo = documento.docu.archi
                    # Obtén el nombre original del archivo
                    nombre_original = os.path.basename(archivo.name)
                    # Ruta completa dentro del ZIP
                    ruta_en_zip = f"{carpeta_aprendiz}{nombre_original}"
                    
                    # Escribe el archivo en el ZIP
                    with archivo.open('rb') as f:
                        zip_file.writestr(ruta_en_zip, f.read())

    # Prepara la respuesta para enviar el archivo ZIP
    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="documentos_grupo_{grupo.id}.zip"'
    
    return response

def crear_grupo(request):
    if request.method == 'GET':
        grupo_form = GrupoForm(user=request.user)
        return render(request, 'grupo_crear.html', {
            'grupo_form': grupo_form
        })
    else:
        try:
            grupo_form = GrupoForm(request.POST, user=request.user)
            if grupo_form.is_valid():
                new_grupo = grupo_form.save(commit=False)
                new_grupo.esta = 'Pre matricula'
                new_grupo.fecha_crea = datetime.now()
                new_grupo.autor = request.user

                # Validar que el centro esté seleccionado
                if not new_grupo.centro:
                    return render(request, 'grupo_crear.html', {
                        'grupo_form': grupo_form,
                        'error': 'Debe seleccionar un centro de formación.'
                    })

                new_grupo.save()

                # Crear la relación gestor-grupo
                perfil = getattr(request.user, 't_perfil', None)
                gestor = T_gestor.objects.get(perfil=perfil)
                T_gestor_grupo.objects.create(
                    fecha_crea=datetime.now(),
                    autor=request.user,
                    gestor=gestor,
                    grupo=new_grupo
                )

                return redirect('pre_matricula')
            else:
                # Si el formulario no es válido, renderizar de nuevo con errores
                print(grupo_form.errors)
                print(grupo_form.cleaned_data)
                print(request.POST)
                return render(request, 'grupo_crear.html', {
                    'grupo_form': grupo_form,
                    'error': 'Por favor, corrige los errores en el formulario.'
                })

        except Exception as e:
            # Capturar cualquier excepción y mostrar un mensaje de error
            return render(request, 'grupo_crear.html', {
                'grupo_form': grupo_form,
                'error': f'Ocurrió un error inesperado: {str(e)}'
            })

def eliminar_grupos(request, id):
    if request.method == 'DELETE':
        try:
            grupo = T_grupo.objects.get(id=id)

            # Verificar si hay aprendices asignados al grupo
            aprendices = T_apre.objects.filter(grupo_id=grupo.id)

            # Verificar si algún aprendiz tiene documentos validados (vali = 1)
            documentos_validados = T_prematri_docu.objects.filter(apren__in=aprendices, vali=1).exists()

            if documentos_validados:
                return JsonResponse({
                    'error': 'No se puede eliminar el grupo porque existen documentos validados para aprendices asignados.'
                }, status=400)

            # Usar una transacción para asegurar la integridad de la base de datos
            with transaction.atomic():
                # Eliminar los registros de t_prematri_docu para los aprendices relacionados
                T_prematri_docu.objects.filter(apren__in=aprendices).delete()

                # Eliminar la relación de los aprendices con el grupo (dejar el campo vacío)
                aprendices.update(grupo=None)

                # Finalmente, eliminar el grupo
                grupo.delete()

            return JsonResponse({'mensaje': 'Grupo y documentos asociados eliminados correctamente.'}, status=200)

        except T_grupo.DoesNotExist:
            return JsonResponse({'error': 'Grupo no encontrado.'}, status=404)
    else:
        return HttpResponseNotAllowed(['DELETE'])
    
def eliminar_relacion_aprendiz_grupos(request, id):
    if request.method == 'DELETE':
        try:
            aprendiz = T_apre.objects.get(id=id)

            # Eliminar todos los registros en t_prematri_docu relacionados al aprendiz
            T_prematri_docu.objects.filter(apren=aprendiz).delete()

            # Desvincular el aprendiz del grupo
            aprendiz.grupo = None
            aprendiz.save()

            return JsonResponse({'mensaje': 'Aprendiz y documentos asociados eliminados correctamente.'}, status=200)

        except T_apre.DoesNotExist:
            return JsonResponse({'error': 'Aprendiz no encontrado.'}, status=404)
    else:
        return HttpResponseNotAllowed(['DELETE'])


def asignar_institucion_gestor(request):
    if request.method == 'GET':
        asignar_insti_form = AsignarInstiForm(user=request.user)
        return render(request, 'asignar_instituciones_gestor.html', {
            'asignar_insti_form': asignar_insti_form
        })
    else:
        try:
            documentos_matricula = [
                        'Carta Intención',
                        'Formato de Inscripción Especial 2025',
                        'Certificado de Aprobacion de Grado Noveno',
                        'Acta de Compromiso de Articulacion',
                        'Acentamiento de matricula',
                        'Formato de diagnostico'
                    ]
            asignar_insti_form = AsignarInstiForm(request.POST, user=request.user)
            perfil = T_perfil.objects.get(user=request.user)
            gestor = T_gestor.objects.get(perfil=perfil)

            if asignar_insti_form.is_valid():
                institucion = asignar_insti_form.cleaned_data['insti']

                # Validar si la institución ya está asignada al gestor actual
                if T_gestor_insti_edu.objects.filter(insti=institucion, gestor=gestor, esta="activo").exists():
                    messages.error(request, 'Esta institución ya está asignada a usted como gestor.')
                    return render(request, 'asignar_instituciones_gestor.html', {
                        'asignar_insti_form': asignar_insti_form,
                    })
                
                # Validar si la institución está asignada a otro gestor
                if T_gestor_insti_edu.objects.filter(insti=institucion, esta="activo").exclude(gestor=gestor).exists():
                    messages.error(request, 'Esta institución ya está asignada a otro gestor.')
                    return render(request, 'asignar_instituciones_gestor.html', {
                        'asignar_insti_form': asignar_insti_form,
                    })

                new_gestor_insti = T_gestor_insti_edu(
                    fecha_regi = datetime.now(),
                    esta = "activo",
                    ano = datetime.now().year,
                    insti = asignar_insti_form.cleaned_data['insti'],
                    seme = '1',
                    gestor = gestor,
                    usuario_asigna = request.user
                )
                insti_edu = T_insti_edu.objects.get(id = institucion.id)
                insti_edu.esta_docu = 'Pendiente'
                insti_edu.save()
                new_gestor_insti.save()
                for documento in documentos_matricula:
                    new_documento = T_insti_docu(
                        nom=documento,
                        insti=asignar_insti_form.cleaned_data['insti'],
                        esta="Pendiente",
                        vali="0"
                    )
                    new_documento.save()

                return redirect('instituciones_gestor')
        except ValueError as e:
            return render(request, 'asignar_instituciones_gestor.html', {
                'asignar_insti_form': asignar_insti_form,
                'error': f'Ocurrió un error: {str(e)}'
            })

class InstiAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Asegúrate de controlar los permisos para que solo usuarios autorizados puedan acceder
        if not self.request.user.is_authenticated:
            return T_insti_edu.objects.none()

        qs = T_insti_edu.objects.all()

        # Filtrar por el término ingresado por el usuario
        if self.q:
            qs = qs.filter(nom__icontains=self.q)  # Ajusta el campo `nombre` según tu modelo

        return qs

# Cargar municipios según el departamento
def cargar_municipios(request):
    departamento_id = request.GET.get('departamento_id')
    if departamento_id:
        municipios = T_munici.objects.filter(nom_departa_id=departamento_id).values('id', 'nom_munici')
        return JsonResponse(list(municipios), safe=False)
    else:
        return JsonResponse({'error': 'El departamento no es válido.'}, status=400)

def cargar_centros(request):
    departamento_id = request.GET.get('departamento_id')
    centros = T_centro_forma.objects.filter(depa_id=departamento_id).values('id', 'nom')
    return JsonResponse(list(centros), safe=False)

# Cargar instituciones según el municipio
def cargar_instituciones(request):
    municipio_id = request.GET.get('municipio_id')
    if municipio_id:
        instituciones = T_insti_edu.objects.filter(muni_id=municipio_id).values('id', 'nom')
        return JsonResponse(list(instituciones), safe=False)
    else:
        return JsonResponse({'error': 'El municipio no es válido.'}, status=400)

@login_required
def instituciones_docs(request, institucion_id):
    # Obtener el perfil del usuario logueado
    perfil = T_perfil.objects.filter(user=request.user).first()
    rol = perfil.rol
    documentos = T_insti_docu.objects.filter(insti=institucion_id)
    institucion = T_insti_edu.objects.get(id=institucion_id)
    total_documentos = 0
    for documento in documentos:
        if  documento.esta == "Cargado":
            total_documentos += 1
    return render(request, 'instituciones_docs.html', { 
        'documentos': documentos, 
        'total_documentos': total_documentos, 
        'institucion': institucion,
        'rol': rol
        })

def cargar_documento_institucion(request, documento_id, institucion_id):
    documento = T_insti_docu.objects.filter(id=documento_id, insti=institucion_id).first()
    
    # Configuración de restricciones
    TAMANO_MAXIMO = 3 * 1024 * 1024  # 3 MB
    TIPOS_PERMITIDOS = ['pdf']  # Extensiones permitidas

    if not documento:
        # Redirige si el documento no pertenece al aprendiz logueado
        return render(request, 'instituciones_gestor.html', {
    })

    if request.method == 'POST' and 'archivo' in request.FILES:

        archivo = request.FILES['archivo']
        extension = archivo.name.split('.')[-1].lower()

        # Validar el tipo de archivo
        if extension not in TIPOS_PERMITIDOS:
            messages.error(request, f"Tipo de archivo no permitido. Los tipos permitidos son: {', '.join(TIPOS_PERMITIDOS)}.")
            return redirect(request.META.get('HTTP_REFERER', '/'))


        # Validar el tamaño del archivo
        if archivo.size > TAMANO_MAXIMO:
            messages.error(request, f"El archivo excede el tamaño máximo permitido de {TAMANO_MAXIMO // (1024 * 1024)} MB.")
            return redirect(request.META.get('HTTP_REFERER', '/'))
        
        ruta = f'documentos/instituciones/{documento.insti.nom}/{archivo.name}' 
        ruta_guardada = default_storage.save(ruta, archivo)

        # Crear un registro en T_docu
        t_docu = T_docu.objects.create(
            nom=archivo.name,
            tipo= archivo.name.split('.')[-1],
            tama = str(archivo.size // 1024) + " KB",
            archi=ruta_guardada,
            priva='No',
            esta='Activo'
        )

        documento.esta = "Cargado"
        documento.docu = t_docu
        documento.fecha_carga = datetime.now()
        documento.usr_carga = request.user
        documento.save()

        # Verificar si todos los documentos de la institución están en estado "Cargado"
        documentos_institucion = T_insti_docu.objects.filter(insti=documento.insti)
        if all(doc.esta == "Cargado" for doc in documentos_institucion):
            # Actualizar el estado de la institución a "Completo"
            institucion = documento.insti
            institucion.esta_docu = "Completo"
            institucion.save()

        return redirect(request.META.get('HTTP_REFERER', '/'))

    return render(request, 'grupos_prematricula.html', {
        })

@login_required
def eliminar_documento_pre_insti(request, documento_id):
    # Obtener el documento
    documentot = get_object_or_404(T_docu, id=documento_id)

    # Obtener el registro de la relación entre documento e institución
    prematri_docu = T_insti_docu.objects.filter(docu_id=documentot.id).first()

    if prematri_docu:
        # Marcar el documento como "Pendiente"
        prematri_docu.esta = 'Pendiente'
        prematri_docu.vali = '0'
        prematri_docu.save()

        # Eliminar el documento físico
        documentot.delete()

        # Verificar si hay documentos no "Cargados" en la institución
        documentos_institucion = T_insti_docu.objects.filter(insti=prematri_docu.insti)
        if any(doc.esta != "Cargado" for doc in documentos_institucion):
            print("Si hay?")
            # Si algún documento no está "Cargado", marcar la institución como "Pendiente"
            institucion = prematri_docu.insti
            institucion.esta_docu = "Pendiente"
            institucion.save()

    # Redirigir después de eliminar el documento
    return redirect(request.META.get('HTTP_REFERER', '/'))
