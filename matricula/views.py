import json
import logging
from django.utils import timezone 
from django.core.serializers.json import DjangoJSONEncoder
from django.db import IntegrityError
from django.utils.timezone import localtime
from django.utils.safestring import mark_safe
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseNotAllowed
from dal import autocomplete
from django.views import generic
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from commons.models import (
    T_ficha,
    T_fase_ficha,
    T_raps,
    T_raps_ficha,
    T_compe,
    T_gestor_depa,
    T_grupo,
    T_docu,
    T_perfil,
    T_histo_docu_insti,
    T_histo_docu_prematri,
    T_insti_edu,
    T_insti_docu,
    T_centro_forma,
    T_munici,
    T_gestor_grupo,
    T_prematri_docu,
    T_apre,
    T_gestor,
    T_gestor_insti_edu
)
from .forms import AsignarAprendicesGrupoForm, GrupoForm, AsignarAprendicesMasivoForm, AsignarInstiForm
from .scripts.cargar_tree import crear_datos_prueba 
from .scripts.cargar_tree_apre import crear_datos_prueba_aprendiz
from django.core.files.storage import default_storage
from datetime import datetime
from django.contrib import messages
from django.db import transaction
from django.db import models
from django.contrib.auth.models import User
import zipfile
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from django.conf import settings
from django.core.files.base import ContentFile
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
            'Documento de Identidad del aprendiz',
            'Registro civil',
            'Certificado de Afiliación de salud',
            'Formato de Tratamiento de Datos del Menor de Edad',
            'Compromiso del Aprendiz',
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
                            aprendiz.esta_docu = "Pendiente"
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
                                    aprendiz.esta_docu = "Pendiente"
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

def obtener_documentos_prematricula(request, aprendiz_id):
    documentos = T_prematri_docu.objects.filter(apren_id=aprendiz_id).values(
        "id", "nom", "esta", "vali", "docu__archi"
    )

    for doc in documentos:
        archivo = doc.get("docu__archi")
        doc["docu_url"] = default_storage.url(archivo) if archivo else None  # Generar la URL

    return JsonResponse(list(documentos), safe=False)

def obtener_historial_prematricula(request, aprendiz_id):
    historial = (
        T_histo_docu_prematri.objects
        .filter(docu_prematri__apren_id=aprendiz_id)
        .order_by("-fecha")
        .values("usu__username", "acci", "docu_prematri__nom", "comen", "fecha")
    )

    historial_list = []
    for h in historial:
        historial_list.append({
            "usuario": h["usu__username"] if h["usu__username"] else "Desconocido",
            "accion": dict(T_histo_docu_prematri.ACCIONES_CHOICES).get(h["acci"], "Desconocida"),
            "documento": h["docu_prematri__nom"],
            "comentario": h["comen"] if h["comen"] else "N/A",
            "fecha": localtime(h["fecha"]).strftime("%Y-%m-%d %H:%M:%S"),  # Convertir a hora local
    })

    return JsonResponse(historial_list, safe=False)

def aprobar_documento_prematricula(request, doc_id):
    if request.method == "POST":
        try:
            documento = T_prematri_docu.objects.get(id=doc_id)
            documento.estado = "Aprobado"
            documento.vali = 4
            documento.save()

            # Registrar en el historial
            T_histo_docu_prematri.objects.create(
                docu_prematri=documento,
                usu=request.user,
                acci="aprobacion",
                comen="Documento aprobado"
            )

            # Obtener el aprendiz relacionado
            aprendiz = documento.apren

            # Verificar si todos los documentos del aprendiz tienen vali = 4
            todos_aprobados = not T_prematri_docu.objects.filter(apren=aprendiz).exclude(vali=4).exists()

            if todos_aprobados:
                aprendiz.esta_docu = "Completo"
                aprendiz.save(update_fields=["esta_docu"])  # Guardar solo este campo

            return JsonResponse({"status": "success", "message": "Documento aprobado correctamente."})
        except T_prematri_docu.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Documento no encontrado."}, status=404)
    return JsonResponse({"status": "error", "message": "Método no permitido."}, status=405)


def rechazar_documento_prematricula(request, doc_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            comentario = data.get("comentario", "").strip()

            if not comentario:
                return JsonResponse({"status": "error", "message": "Debe ingresar un motivo de rechazo."}, status=400)

            documento = T_prematri_docu.objects.get(id=doc_id)
            documento.esta = "Rechazado"
            documento.vali = 2
            documento.save()

            T_histo_docu_prematri.objects.create(
                docu_prematri=documento,
                usu=request.user,
                acci="rechazo",
                comen=comentario
            )

            return JsonResponse({"status": "success", "message": "Documento rechazado correctamente."})
        except T_prematri_docu.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Documento no encontrado."}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Error en el formato de los datos."}, status=400)

    return JsonResponse({"status": "error", "message": "Método no permitido."}, status=405)


def dividir_pdf(request):
    if request.method == 'POST':
        if 'pdf_file' not in request.FILES:
            return JsonResponse({"error": "No se ha subido ningún archivo PDF."}, status=400)
        
        pdf_file = request.FILES['pdf_file']

        if not pdf_file.name.endswith('.pdf'):
            return JsonResponse({"error": "Por favor, suba un archivo PDF válido."}, status=400)

        try:
            pdf_reader = PdfReader(pdf_file)

            if len(pdf_reader.pages) == 0:
                return JsonResponse({"error": "El archivo PDF está vacío."}, status=400)
            
            # Crear el ZIP en memoria
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for page_num in range(len(pdf_reader.pages)):
                    pdf_writer = PdfWriter()
                    pdf_writer.add_page(pdf_reader.pages[page_num])

                    pdf_bytes = io.BytesIO()
                    pdf_writer.write(pdf_bytes)

                    pdf_name = f"pagina_{page_num + 1}.pdf"
                    zip_file.writestr(pdf_name, pdf_bytes.getvalue())
            
            zip_buffer.seek(0)

            # Guardar el ZIP en media/temp
            zip_path = f"temp/paginas_separadas_{pdf_file.name.replace('.pdf', '')}.zip"
            full_path = os.path.join(settings.MEDIA_ROOT, zip_path)
            default_storage.save(zip_path, ContentFile(zip_buffer.getvalue()))

            download_url = f"{settings.MEDIA_URL}{zip_path}"

            return JsonResponse({
                "success": True,
                "message": "PDF dividido exitosamente.",
                "total_paginas": len(pdf_reader.pages),
                "download_url": download_url
            })

        except Exception as e:
            print(f"Error interno: {e}")
            return JsonResponse({"error": f"Ocurrió un error al procesar el PDF: {str(e)}"}, status=500)

    return JsonResponse({"error": "Método no permitido."}, status=405)

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
    documento.fecha_apro = timezone.now()
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
    total_instituciones_aprobadas = T_insti_edu.objects.filter(esta_docu="Completo").distinct().count()
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
        'total_instituciones_aprobadas': total_instituciones_aprobadas,
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
    estados = T_insti_edu.objects.values_list('esta_docu', flat=True).distinct()
    return JsonResponse(list(estados), safe=False)

def obtener_opciones_sectores(request):
    sectores = T_insti_edu.objects.values_list('secto', flat=True).distinct()
    return JsonResponse(list(sectores), safe=False)

# Listado filtrado
def filtrar_instituciones_gestor(request):
    municipio = request.GET.getlist('municipio_filtro', [])
    estado = request.GET.getlist('estado_filtro', [])
    sector = request.GET.getlist('sector_filtro', [])

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
        instituciones = instituciones.filter(insti__esta_docu__in=estado)
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
            'gestor': i.gestor.perfil.nom+" "+i.gestor.perfil.apelli,
            'detalle_url': reverse('instituciones_docs', args=[i.insti.id])  # Genera la URL
        }
        for i in instituciones
    ]
    return JsonResponse(resultados, safe=False)

def eliminar_institucion_gestor(request, id):
    if request.method == 'POST':
        try:
            institucion_gest = get_object_or_404(T_gestor_insti_edu , id=id)
            id_institucion = institucion_gest.insti.id

            # Verificar si hay registros en T_grupo relacionados con la institución
            grupos_asociados = T_grupo.objects.filter(insti_id=id_institucion).exists()

            if grupos_asociados:
                return JsonResponse({'status':'error','message': 'No se puede eliminar la institución porque tiene grupos asociados.'}, status=400)

            # Eliminar documentos asociados en T_insti_docu
            T_insti_docu.objects.filter(insti_id=id_institucion).delete()

            # Eliminar la institución gestora
            institucion_gest.delete()

            return JsonResponse({'status':'success','message': 'Institución y documentos asociados eliminados correctamente.'}, status=200)

        except T_gestor_insti_edu.DoesNotExist:
            return JsonResponse({'status':'error','message': 'Institución no encontrada.'}, status=404)
    return JsonResponse({'status': 'error', 'message':'Método no permitido'}, status = 405)

def cargar_documento_prematricula(request, documento_id):
    # Restricciones
    TAMANO_MAXIMO = 3 * 1024 * 1024  # 3 MB
    TIPOS_PERMITIDOS = ['pdf']

    # Obtener el documento
    documento = get_object_or_404(T_prematri_docu, id=documento_id)

    if request.method == 'POST':

        archivo = request.FILES.get("documento")

        if not archivo:
            return JsonResponse({"status": "error", "message": "No se recibió ningún archivo."}, status=400)

        extension = archivo.name.split('.')[-1].lower()

        # Validar el tipo de archivo
        if extension not in TIPOS_PERMITIDOS:
            return JsonResponse({
                "status": "error",
                "message": f"Tipo de archivo no permitido. Solo se permiten: {', '.join(TIPOS_PERMITIDOS)}."
            }, status=400)

        # Validar el tamaño del archivo
        if archivo.size > TAMANO_MAXIMO:
            return JsonResponse({
                "status": "error",
                "message": f"El archivo excede el tamaño máximo permitido de {TAMANO_MAXIMO // (1024 * 1024)} MB."
            }, status=400)

        # Generar la ruta de almacenamiento
        ruta = f'documentos/aprendices/prematricula/{documento.apren.perfil.nom}{documento.apren.perfil.apelli}{documento.apren.perfil.dni}/{archivo.name}'

        # Guardar el archivo
        ruta_guardada = default_storage.save(ruta, archivo)

        # Crear un nuevo registro en T_docu
        t_docu = T_docu.objects.create(
            nom=archivo.name,
            tipo=extension,
            tama=f"{archivo.size // 1024} KB",
            archi=ruta_guardada,
            priva='No',
            esta='Activo'
        )

        print(f"Valor actual de documento.vali: {documento.vali}")

        if int(documento.vali) == 2:  # Asegurar que es un entero
            nuevo_estado_text = "recarga"
            nuevo_estado = 3
            accion_historial = 'recarga'
            comentario_historial = 'Documento recargado tras rechazo.'
        else:
            nuevo_estado_text = "cargado"
            nuevo_estado = 1
            accion_historial = 'carga'
            comentario_historial = 'Documento subido.'

        # Actualizar el documento en T_prematri_docu
        documento.esta = nuevo_estado_text
        documento.vali = nuevo_estado
        documento.docu = t_docu
        documento.save()
        print(f"Valor guardado de documento.vali: {documento.vali}")

        # Registrar en el historial
        T_histo_docu_prematri.objects.create(
            docu_prematri=documento,
            usu=request.user,
            acci=accion_historial,
            comen=comentario_historial
        )

        return JsonResponse({
            "status": "success",
            "message": "Documento subido y registrado en historial."
        }, status=200)

    return JsonResponse({"status": "error", "message": "Método no permitido."}, status=405)


@login_required  # Funcion para eliminar documento de prematricula aprendiz
def eliminar_documento_prematricula(request, documento_id):
    if request.method != "DELETE":
        return JsonResponse({"status": "error", "error": "Método no permitido"}, status=405)

    documento = get_object_or_404(T_prematri_docu, id=documento_id)

    T_histo_docu_prematri.objects.create(
        docu_prematri=documento,
        usu=request.user,
        acci="eliminacion",
        comen="Documento eliminado"
    )

    if documento.docu:
        archivo_a_eliminar = documento.docu.archi.name
        documento.docu.delete()
        if archivo_a_eliminar:
            default_storage.delete(archivo_a_eliminar)


    documento.docu = None
    documento.esta = "Pendiente"
    documento.vali = 0
    documento.save()

    return JsonResponse({"status": "success", "message": "Eliminado correctamente"}, status = 200)

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
                new_grupo.fecha_crea = timezone.now()
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
                    fecha_crea=timezone.now(),
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

            return JsonResponse({"success": True, "mensaje": "Aprendiz y documentos asociados eliminados correctamente."}, status=200)

        except T_apre.DoesNotExist:
            return JsonResponse({"success": False, "mensaje": "Aprendiz no encontrado."}, status=404)
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
                        'Certificado de Aprobación de Grado Noveno',
                        'Formato de autodiagnóstico'
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
                    fecha_regi = timezone.now(),
                    esta = "activo",
                    ano = timezone.now().year,
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
        if  documento.vali == "4":
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
        documento.fecha_carga = timezone.now()
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

# Configurar logs para depuración
logger = logging.getLogger(__name__)

def cargar_documentos_institucion_multiples(request, institucion_id):
    if request.method == "POST":
        print(request.FILES)
        print(request.POST)
        TAMANO_MAXIMO = 3 * 1024 * 1024  # 3 MB
        TIPOS_PERMITIDOS = ['pdf']  # Extensiones permitidas
        archivos_subidos = 0
        errores = []

        logger.info("Recibiendo solicitud de carga múltiple...")

        if not request.FILES:
            errores.append("No se enviaron archivos.")
            logger.warning("No se recibieron archivos en la petición.")
            return JsonResponse({"errors": errores}, status=400)

        for key, archivo in request.FILES.items():
            logger.info(f"Procesando archivo: {archivo.name}")

            if key.startswith("archivo_"):

                documento_nom = request.POST.get(f"{key}_name")
                documento_id = key.split("_")[1]
                documento = T_insti_docu.objects.filter(id=documento_id, insti_id=institucion_id).first()

                if not documento:
                    errores.append(f"Documento con ID {documento_id} no encontrado.")
                    logger.warning(f"Documento {documento_id} no encontrado.")
                    continue

                # Validar tipos de archivo según el nombre del documento
                if documento_nom == "Formato de Inscripción Especial 2025":
                    TIPOS_PERMITIDOS = ['xls', 'xlsx']
                else:
                    TIPOS_PERMITIDOS = ['pdf']

                extension = archivo.name.split('.')[-1].lower()

                if extension not in TIPOS_PERMITIDOS:
                    errores.append(f"El archivo {archivo.name} tiene una extensión no permitida: {extension}")
                    continue

                if archivo.size > TAMANO_MAXIMO:
                    errores.append(f"El archivo {archivo.name} excede el tamaño máximo de {TAMANO_MAXIMO // (1024 * 1024)} MB.")
                    continue

                # Construir la ruta de almacenamiento
                ruta = f'documentos/instituciones/{documento.insti.nom}/{archivo.name}'

                # Verificar si el archivo ya existe y renombrarlo
                contador = 1
                nombre_base, extension_archivo = os.path.splitext(archivo.name)
                while default_storage.exists(ruta):
                    ruta = f'documentos/instituciones/{documento.insti.nom}/{nombre_base}_{contador}{extension_archivo}'
                    contador += 1

                ruta_guardada = default_storage.save(ruta, archivo)
                logger.info(f"Archivo {archivo.name} guardado en {ruta_guardada}")

                # Crear el registro en T_docu
                t_docu = T_docu.objects.create(
                    nom=archivo.name,
                    tipo=extension,
                    tama=f"{archivo.size // 1024} KB",
                    archi=ruta_guardada,
                    priva='No',
                    esta='Activo'
                )

                # Determinar nuevo estado del documento
                if documento.vali == "2":  # Si estaba Rechazado
                    documento.esta = "Recargado"
                    documento.vali = "3"  # Estado "Recargado"
                else:
                    documento.esta = "Cargado"
                    documento.vali = "1"  # Estado "Cargado"

                # Asignar el nuevo documento
                documento.docu = t_docu
                documento.save()
                archivos_subidos += 1

                # Registrar en el historial
                T_histo_docu_insti.objects.create(
                    docu_insti=documento,
                    usu=request.user,
                    acci='recarga' if documento.vali == "3" else 'carga',
                    comen='Documento recargado' if documento.vali == "3" else ''
                )

        # Verificar si todos los documentos de la institución están en estado "Cargado" o "Recargado"
        documentos_institucion = T_insti_docu.objects.filter(insti_id=institucion_id)
        if all(doc.esta in ["Cargado", "Recargado"] for doc in documentos_institucion):
            institucion = documentos_institucion.first().insti
            institucion.esta_docu = "Completo"
            institucion.save()
            logger.info(f"Todos los documentos de la institución {institucion.nom} han sido cargados. Estado actualizado a 'Completo'.")

        response = {
            "message": f"{archivos_subidos} archivos cargados correctamente.",
            "errors": errores,
            "archivos_cargados": archivos_subidos,  # Número de archivos exitosos
        }

        logger.info(f"Respuesta JSON: {response}")
        return JsonResponse(response)

    return JsonResponse({"error": "Método no permitido"}, status=405)


def rechazar_documento_insti(request, docu_id, insti_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        motivo = data.get('motivo', '')

        documento = T_insti_docu.objects.get(id=docu_id, insti_id=insti_id)
        documento.vali = 2
        documento.esta = "Rechazado"
        documento.save()

        T_histo_docu_insti.objects.create(
            docu_insti=documento,
            usu=request.user,
            acci='rechazo',
            comen=motivo
        )

        return JsonResponse({'status': 'success', 'message': 'Registrado'})

    return JsonResponse({'error': 'Método no permitido'}, status=405)

def confirmar_documento_insti(request, documento_id, institucion_id):
    institucion = T_insti_edu.objects.get(id=institucion_id)
    documento = T_insti_docu.objects.get(id=documento_id)    
    documento.vali = "4"
    documento.esta = "Aprobado"
    documento.save()

    T_histo_docu_insti.objects.create(
    docu_insti=documento,
    usu=request.user,
    acci='aprobacion',
    comen=''
    )
    
    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def eliminar_documento_pre_insti(request, documento_id):
    # Obtener el documento
    documento = get_object_or_404(T_docu, id=documento_id)

    # Obtener la relación del documento con la institución
    docu_insti = T_insti_docu.objects.filter(docu_id=documento.id).first()

    if docu_insti:
        T_histo_docu_insti.objects.create(
            docu_insti=docu_insti,
            usu=request.user, 
            acci="eliminacion",
            comen=f"Documento '{documento.nom}' eliminado por {request.user.username}."
        )

        # Marcar el documento como "Pendiente"
        docu_insti.esta = "Pendiente"
        docu_insti.vali = "0"
        docu_insti.save()

        # Eliminar el archivo físico del documento
        documento.delete()

        documentos_institucion = T_insti_docu.objects.filter(insti=docu_insti.insti)
        if any(doc.esta != "Cargado" for doc in documentos_institucion):
            institucion = docu_insti.insti
            institucion.esta_docu = "Pendiente"
            institucion.save()

    # Redirigir después de eliminar el documento
    return redirect(request.META.get('HTTP_REFERER', '/'))

def obtener_historial_institucion(request, institucion_id):
    historial = T_histo_docu_insti.objects.filter(docu_insti__insti_id=institucion_id).order_by('-id')
    
    data = [
        {
            "usuario": histo.usu.username,
            "accion": histo.acci,
            "documento": histo.docu_insti.nom,
            "comentario": histo.comen if histo.comen else "Sin comentario",
            "fecha": localtime(histo.fecha).strftime("%Y-%m-%d %H:%M:%S")
        }
        for histo in historial
    ]
    
    return JsonResponse({"historial": data})

def formalizar_ficha(request):
    if request.method == "POST":
        try:
            print(request.POST)
            data = json.loads(request.body)
            grupo_id = data.get("grupo_id")
            numero_ficha = data.get("numero_ficha")

            if T_ficha.objects.filter(num=numero_ficha).exists():
                return JsonResponse({'status': 'error', 'message': 'Ya existe una ficha con el número ingresado.'}, status=400)
            
            grupo = T_grupo.objects.get(id=grupo_id)
            grupo.esta = "Formalizado"
            grupo.save()


            total_aprendices = T_apre.objects.filter(grupo=grupo).count()
            total_formalizados = T_apre.objects.filter(grupo=grupo, esta_docu="Completo").count()
            total_pendientes = T_apre.objects.filter(grupo=grupo, esta_docu="Pendiente").count()

            ficha = T_ficha.objects.create(
                num=numero_ficha,
                grupo=grupo,
                fecha_aper=timezone.now(),
                fecha_cierre=None,
                insti=grupo.insti,
                centro=grupo.centro,
                progra=grupo.progra,
                num_apre_proce=total_aprendices,
                num_apre_forma=total_formalizados,
                num_apre_pendi_regi=total_pendientes,
                esta="Activo"
            )

            T_fase_ficha.objects.create(
                fase = "analisis",
                ficha = ficha,
                fecha_ini = timezone.now(),
                instru = None,
                vige  = 1
            )

            raps = T_raps.objects.filter(compe__in = T_compe.objects.filter(progra = ficha.progra))
            T_raps_ficha.objects.bulk_create([T_raps_ficha(ficha = ficha, rap = rap) for rap in raps])

            T_apre.objects.filter(grupo=grupo).update(ficha=ficha)

            crear_datos_prueba(ficha.id)

            aprendices = T_apre.objects.filter(ficha=ficha)
            for aprendiz in aprendices:
                crear_datos_prueba_aprendiz(aprendiz.id)

            return JsonResponse({'status': 'success', 'message': 'Ficha creada con éxito.'})

        except T_grupo.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'El grupo no existe.'}, status=404)

        except IntegrityError as e:
            return JsonResponse({'status': 'error', 'message': 'Error de integridad: ' + str(e)}, status=400)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)
