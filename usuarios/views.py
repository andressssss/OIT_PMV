import re
import unicodedata
from io import StringIO
from django.utils.encoding import force_str
from django.views.decorators.http import require_POST, require_GET
from django.forms import ValidationError
from django.contrib.auth.hashers import make_password
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.files.storage import default_storage
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils import timezone
from commons.models import (
    T_instru, 
    T_ficha, 
    T_cuentas, 
    T_gestor_insti_edu,
    T_apre,
    T_docu_labo,
    T_gestor_depa,
    T_gestor,
    T_docu,
    T_perfil,
    T_admin,
    T_lider,
    T_nove,
    T_repre_legal,
    T_munici,
    T_departa,
    T_insti_edu,
    T_centro_forma,
    T_progra
    )
from .forms import InstructorForm, PerfilEForm,CargarInstructoresMasivoForm, CustomPasswordChangeForm, DocumentoLaboralForm, GestorForm, PerfilEditForm, GestorDepaForm, CargarAprendicesMasivoForm, UserFormCreate, UserFormEdit, PerfilForm, NovedadForm, AdministradoresForm, AprendizForm, LiderForm, RepresanteLegalForm, DepartamentoForm, MunicipioForm, InstitucionForm, CentroFormacionForm
from django.db import IntegrityError
from django.http import HttpResponseRedirect, JsonResponse
from .serializers import T_insti_edu_Serializer
from rest_framework.views import APIView
from django.db.models.functions import Cast
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.forms.models import model_to_dict
from django.db.models.functions import TruncDate
from io import TextIOWrapper
from django.core.validators import validate_email
from django.core.mail import send_mail
from django.db.models import Q, F, Func, DateField  # Para realizar búsquedas dinámicas
from django.conf import settings
from datetime import datetime
from django.db.models import Prefetch
from django.contrib import messages
from django.db import transaction
from django.utils.html import escape
from django.core.paginator import Paginator
from django.views.decorators.cache import never_cache
from django.db.models.functions import Lower
import csv
import random
import string
import json
import logging
logger = logging.getLogger(__name__)

from django.conf import settings
print("TEMPLATES_DIR:", settings.TEMPLATES[0]['DIRS'])

def home(request):
    return render(request, 'home.html')

@never_cache
def signin(request):
    if request.user.is_authenticated:
        return redirect('home')  # Reemplaza 'home' por la ruta real si cambia

    if request.method == 'GET':
        return render(request, 'signin.html', {
            'form': AuthenticationForm()
        })
    else:
        # Autenticación del usuario
        user = authenticate(
            request, username=request.POST['username'], password=request.POST['password'])

        if user is None:
            return render(request, 'signin.html', {
                'form': AuthenticationForm(),
                'error': "El usuario o la contraseña es incorrecto"
            })
        else:
            login(request, user)

            try:
                perfil = T_perfil.objects.get(user=user)
                if perfil.rol == 'aprendiz':
                    return redirect('panel_aprendiz')
                elif perfil.rol in ['gestor', 'lider']:
                    return redirect('instituciones_gestor')
                elif perfil.rol == 'admin':
                    return redirect('admin_dashboard')
                elif perfil.rol == 'instructor':
                    return redirect('fichas')
            except T_perfil.DoesNotExist:
                pass

            return redirect('novedades')

@require_GET
def consultar_usuario_por_cedula(request):
    cedula = request.GET.get('cedula')

    if not cedula:
        return JsonResponse({'error': 'Cédula no proporcionada'}, status=400)

    perfil = T_perfil.objects.filter(dni=cedula).first()

    if perfil is None:
        return JsonResponse({'error': 'No se encontró un usuario con esa cédula'}, status=404)

    return JsonResponse({'username': perfil.user.username})


def signup(request):
    if request.method == 'GET':
        return render(request, 'signup.html')
    else:
        if request.POST['password1'] == request.POST['password2']:
            try:
                email = request.POST['correo']
                if User.objects.filter(email=email).exists():
                    return render(request, 'signup.html', {
                        'error': "El correo ya existe"
                    })
                new_user = User(
                    username=request.POST['username'], 
                    email = request.POST['correo'],
                    first_name = request.POST['nombre'],
                    last_name = request.POST['apellido']
                )
                new_user.set_password(request.POST['password1'])
                new_user.save()
                new_perfil = T_perfil(
                    nom = request.POST['nombre'],
                    apelli= request.POST['apellido'],
                    tipo_dni= request.POST['tipoi'],
                    dni= request.POST['dni'],
                    tele= request.POST['tele'],
                    dire= request.POST['dire'],
                    mail = request.POST['correo'],
                    gene= request.POST['gene'],
                    fecha_naci= request.POST['fechanaci'],
                    rol = 'instructor',
                    user = new_user
                )
                new_perfil.save()
                new_instru = T_instru(
                    esta = 'inscrito',
                    perfil = new_perfil,
                    tipo_vincu = 'web'
                )
                new_instru.save()
                return redirect('signin')
            except IntegrityError:
                return render(request, 'signup.html', {
                    'error': "El usuario ya existe"
                })
    return render(request, 'signup.html', {
        'error': "Las contraseñas no coinciden"
    })

def check_authentication(request):
    is_authenticated = request.user.is_authenticated
    return JsonResponse({'isAuthenticated': is_authenticated})

@login_required
def perfil(request):
    perfil = getattr(request.user, 't_perfil', None)
    usuario = None

    if perfil.rol == 'instructor':
        usuario = T_instru.objects.get(perfil=perfil)
    elif perfil.rol == 'aprendiz':
        usuario = T_apre.objects.get(perfil=perfil)
    elif perfil.rol == 'lider':
        usuario = T_lider.objects.get(perfil=perfil)
    elif perfil.rol == 'admin':
        usuario = T_admin.objects.get(perfil=perfil)
    elif perfil.rol == 'gestor':
        usuario = T_gestor.objects.get(perfil=perfil)
    elif perfil.rol == 'cuentas':
        usuario = T_cuentas.objects.get(perfil=perfil)

    # Mostrar documentos laborales
    documentos = T_docu_labo.objects.filter(usu=request.user, tipo='laboral')

    # Mostrar documentos laborales
    documentos_aca = T_docu_labo.objects.filter(usu=request.user, tipo='academico')

    # Obtener la hoja de vida del usuario (si existe)
    hoja_vida = T_docu_labo.objects.filter(usu=request.user, tipo='hv').first()

    # Inicializar los formularios por defecto
    form_contraseña = CustomPasswordChangeForm(user=request.user)
    form_documento = DocumentoLaboralForm()
    form_perfil = PerfilForm(instance=perfil)

    # Manejo de las solicitudes POST
    if request.method == 'POST':
        if 'old_password' in request.POST:
            form_contraseña = CustomPasswordChangeForm(user=request.user, data=request.POST)
            if form_contraseña.is_valid():
                form_contraseña.save()
                update_session_auth_hash(request, form_contraseña.user)  # Mantener la sesión activa con la nueva contraseña
                logout(request)  # Cerrar sesión para forzar al usuario a iniciar sesión nuevamente

                # Si es una solicitud AJAX, enviar la respuesta adecuada con SweetAlert
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'success', 'message': 'Cambio satisfactorio, inicie sesión nuevamente.'})
                else:
                    return redirect('login')  # Si no es AJAX, redirigir al inicio de sesión
            else:
                # Responder con los errores en formato JSON (cuando es AJAX)
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'errors': form_contraseña.errors})
                else:
                    messages.error(request, 'Por favor corrige los errores a continuación.')
        elif request.POST.get('form_id') == 'documento_form':
            form_documento = DocumentoLaboralForm(request.POST, request.FILES)
            if form_documento.is_valid():
                # Obtener el archivo cargado
                archivo = request.FILES['documento']

                # Ruta de almacenamiento del archivo
                ruta = f'documentos/instructores/{usuario.perfil.nom}{usuario.perfil.apelli}{usuario.perfil.dni}/laboral/{archivo.name}'
                ruta_guardada = default_storage.save(ruta, archivo)

                # Crear el registro en T_docu
                t_docu = T_docu.objects.create(
                    nom=archivo.name,
                    tipo=archivo.name.split('.')[-1],
                    tama=str(archivo.size // 1024) + " KB",  # Tamaño en KB
                    archi=ruta_guardada,
                    priva='No',  # O cualquier valor adecuado
                    esta='Activo'  # O cualquier estado inicial adecuado
                )

                # Guardar el formulario de DocumentoLaboralForm (sin guardar aún)
                documento = form_documento.save(commit=False)
                documento.usu = request.user  # Asociar el documento al usuario actual
                documento.esta = 'Cargado'  # Estado inicial del documento
                documento.docu = t_docu  # Asignar el documento de T_docu
                documento.tipo = 'laboral'  # Asignar el documento de T_docu
                documento.save()  # Guardar el documento
                messages.success(request, "Documento guardado satisfactoriamente.")

                # Redirigir al perfil después de guardar
                return redirect(request.META.get('HTTP_REFERER', '/'))
            else:
                print(form_documento.errors)  # Imprimir errores para depuración
                messages.error(request, 'Por favor, corrige los errores en el formulario.')

        elif request.POST.get('form_id') == 'documento_aca_form':
            form_documento = DocumentoLaboralForm(request.POST, request.FILES)
            if form_documento.is_valid():

                # Obtener el archivo cargado
                archivo = request.FILES['documento']

                # Ruta de almacenamiento del archivo
                ruta = f'documentos/instructores/{usuario.perfil.nom}{usuario.perfil.apelli}{usuario.perfil.dni}/academico/{archivo.name}'
                ruta_guardada = default_storage.save(ruta, archivo)

                # Crear el registro en T_docu
                t_docu = T_docu.objects.create(
                    nom=archivo.name,
                    tipo=archivo.name.split('.')[-1],
                    tama=str(archivo.size // 1024) + " KB",  # Tamaño en KB
                    archi=ruta_guardada,
                    priva='No',  # O cualquier valor adecuado
                    esta='Activo'  # O cualquier estado inicial adecuado
                )

                # Guardar el formulario de DocumentoLaboralForm (sin guardar aún)
                documento = form_documento.save(commit=False)
                documento.usu = request.user  # Asociar el documento al usuario actual
                documento.esta = 'Cargado'  # Estado inicial del documento
                documento.docu = t_docu  # Asignar el documento de T_docu
                documento.tipo = 'academico'  # Asignar el documento de T_docu
                documento.save()  # Guardar el documento
                messages.success(request, "Documento guardado satisfactoriamente.")

                # Redirigir al perfil después de guardar
                return redirect(request.META.get('HTTP_REFERER', '/'))
            else:
                print(form_documento.errors)  # Imprimir errores para depuración
                messages.error(request, 'Por favor, corrige los errores en el formulario.')
        elif 'cv_file' in request.FILES:
            archivo = request.FILES['cv_file']

            # Ruta de almacenamiento del archivo
            ruta = f'documentos/instructores/{usuario.perfil.nom}{usuario.perfil.apelli}{usuario.perfil.dni}/HV/{archivo.name}'
            ruta_guardada = default_storage.save(ruta, archivo)

            # Crear el registro en T_docu
            t_docu = T_docu.objects.create(
                nom=archivo.name,
                tipo=archivo.name.split('.')[-1],
                tama=str(archivo.size // 1024) + " KB",  # Tamaño en KB
                archi=ruta_guardada,
                priva='No',  # O cualquier valor adecuado
                esta='Activo'  # O cualquier estado inicial adecuado
            )

            # Guardar el formulario de DocumentoLaboralForm (sin guardar aún)
            documento = form_documento.save(commit=False)
            documento.usu = request.user  # Asociar el documento al usuario actual
            documento.esta = 'Cargado'  # Estado inicial del documento
            documento.docu = t_docu  # Asignar el documento de T_docu
            documento.tipo = 'hv'  # Asignar el documento de T_docu
            documento.nom = 'Hoja de Vida'  # Asignar el documento de T_docu
            documento.cate = 'hv'  # Asignar el documento de T_docu
            documento.save()  # Guardar el documento
            messages.success(request, "Documento guardado satisfactoriamente.")

            # Redirigir al perfil después de guardar
            return redirect(request.META.get('HTTP_REFERER', '/'))
        
        elif request.POST.get('form_id') == 'perfil_form':  # Actualización de perfil
            logger.warning("llega?")
            form_perfil = PerfilForm(request.POST, instance=request.user.t_perfil)

            if form_perfil.is_valid():
                datos_actualizados = form_perfil.cleaned_data
                logger.warning(datos_actualizados)

                if 'fecha_naci' not in datos_actualizados or datos_actualizados['fecha_naci'] is None:
                    logger.warning("No viene fecha")
                    perfil_fe = T_perfil.objects.get(id = request.user.t_perfil.id)
                    form_perfil.instance.fecha_naci = perfil_fe.fecha_naci
                    logger.warning(form_perfil.instance.fecha_naci)
                form_perfil.save()
                
            # Manejo del correo electrónico
            nuevo_email = form_perfil.cleaned_data.get('mail')
            if nuevo_email:
                usuario_act = User.objects.get(id=request.user.id)
                usuario_act.email = nuevo_email
                usuario_act.save()

                request.user.refresh_from_db()
                #request.user.save()  # Guardar el nuevo correo en auth_user
                messages.success(request, "Correo electrónico actualizado correctamente.")
            return redirect('perfil')
        else:
            print(form_documento.errors)  # Imprimir errores para depuración
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
            
        
    form_perfil = PerfilForm(instance=request.user.t_perfil)
    form_documento = DocumentoLaboralForm()
    form_contraseña = CustomPasswordChangeForm(user=request.user)
    return render(request, 'perfil.html', {
        'usuario': usuario,
        'form_contraseña': form_contraseña,
        'form_documento': form_documento,
        'documentos': documentos,
        'documentos_aca': documentos_aca,
        'hoja_vida': hoja_vida,
        'form_perfil': form_perfil
    })

@login_required
def editar_perfil(request):
    perfil = getattr(request.user, 't_perfil', None)
    if request.method == 'POST':
        print("Si llega!")
        form = PerfilEForm(request.POST, instance=perfil)
        if form.is_valid():
            form.save()
            return redirect(request.META.get('HTTP_REFERER', '/'))
    else:
        form = PerfilEForm(instance=perfil)  # Pre-poblar el formulario con los datos actuales del perfil
    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def eliminar_documentoinstru(request, hv_id):
    archivo = get_object_or_404(T_docu_labo, id=hv_id)
    documento = get_object_or_404(T_docu, id=archivo.docu.id)
    mensaje = archivo.tipo
    if mensaje == 'laboral':
        mensaje = "Documento eliminado"
    elif mensaje == 'academico':
        mensaje = "Documento eliminado"
    elif mensaje == 'hv':
        mensaje = "Hoja de vida eliminada"
    
    archivo.delete()
    documento.delete()
    messages.success(request, mensaje)
    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def signout(request):
    logout(request)
    return redirect('home')

@login_required
def dashboard_admin(request):
    perfil = getattr(request.user, 't_perfil', None)
    rol = perfil.rol
    return render(request, 'admin_dashboard.html', {'rol':rol})

### INSTRUCTORES ###

@login_required
def instructores(request):
    instructores = T_instru.objects.select_related('perfil').all()
    fichas = T_ficha.objects.all()
    programas = T_progra.objects.all()
    perfil_form = PerfilForm()
    instructor_form = InstructorForm()
    return render(request, 'instructor.html', {
        'instructores': instructores,
        'perfil_form': perfil_form,
        'instructor_form': instructor_form,
        'fichas': fichas,
        'programas': programas
    })
        
@login_required
def crear_instructor(request):
    if request.method == 'POST':
        perfil_form = PerfilForm(request.POST)
        instructor_form = InstructorForm(request.POST)
        ficha_ids = request.POST.getlist('ficha_id[]')
        ficha = None

        if perfil_form.is_valid() and instructor_form.is_valid():
            dni = perfil_form.cleaned_data.get('dni')
            email = perfil_form.cleaned_data.get('mail')
            
            if T_perfil.objects.filter(dni__iexact = dni).exists():
                return JsonResponse({'status': 'error', 'message': 'Ya existe un usuario con ese DNI'}, status = 400)
            
            if T_perfil.objects.filter(mail__iexact = email).exists():
                return JsonResponse({'status': 'error', 'message': 'Ya existe un usuario con ese email'}, status = 400)

            nombre = perfil_form.cleaned_data['nom']
            apellido = perfil_form.cleaned_data['apelli']
            base_username = (nombre[:3] + apellido[:3]).lower()
            username = base_username
            i = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{i}"
                i += 1

            # contraseña = generar_contraseña()

            new_user = User.objects.create_user(
                username=username,
                password=str(dni),
                email=perfil_form.cleaned_data['mail']
            )

            new_perfil = perfil_form.save(commit=False)
            new_perfil.user = new_user
            new_perfil.rol = 'instructor'
            new_perfil.mail = new_user.email
            new_perfil.save()
                    
                    
            new_instructor = instructor_form.save(commit=False)
            new_instructor.perfil = new_perfil
            new_instructor.esta = "Activo"
            new_instructor.save()
            
            for ficha_id in ficha_ids:
                try:
                    ficha = T_ficha.objects.get(id = ficha_id)
                    if ficha.instru is not None:
                        return JsonResponse({
                            'status': 'error',
                            'message': f'La ficha {ficha.num} ya tiene un instructor asignado: {ficha.instru.perfil.nom} {ficha.instru.perfil.apelli}'
                        }, status = 409)
                    ficha.instru = new_instructor
                    ficha.save()
                except T_ficha.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'La ficha con ID {ficha_id} no existe.'
                    }, status=404)

            return JsonResponse({'status': 'success', 'message': 'Instructor creado con éxito.'})
        else:
            errores_dict = {
                **perfil_form.errors.get_json_data(),
                **instructor_form.errors.get_json_data()
            }
            errores_custom = []

            for field, errors_list in errores_dict.items():
                if field in perfil_form.fields:
                    nombre_campo = perfil_form.fields[field].label or field.capitalize()
                elif field in instructor_form.fields:
                    nombre_campo = instructor_form.fields[field].label or field.capitalize()
                else:
                    nombre_campo = field.capitalize()

                for err in errors_list:
                    mensaje = f"{nombre_campo}: {err['message']}"
                    errores_custom.append(mensaje)


            return JsonResponse({'status': 'error', 'message':'Errores en el formulario', 'errors': '<br>'.join(errores_custom)}, status = 400)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

@login_required
def obtener_instructor(request, instructor_id):
    instructor = T_instru.objects.filter(id=instructor_id).select_related('perfil').first()

    if instructor:
        fichas = T_ficha.objects.filter(instru=instructor)
        data = {
            'id': instructor.id,
            'perfil': {
                'nom': instructor.perfil.nom,
                'apelli': instructor.perfil.apelli,
                'tipo_dni': instructor.perfil.tipo_dni,
                'dni': instructor.perfil.dni,
                'tele': instructor.perfil.tele,
                'dire': instructor.perfil.dire,
                'mail': instructor.perfil.mail,
                'gene': instructor.perfil.gene,
                'fecha_naci': instructor.perfil.fecha_naci.isoformat() if instructor.perfil.fecha_naci else ''
            },
            'contra': instructor.contra,
            'profe': instructor.profe,
            'fecha_ini': instructor.fecha_ini.isoformat() if instructor.fecha_ini else '',
            'fecha_fin': instructor.fecha_fin.isoformat() if instructor.fecha_fin else '',
            'tipo_vincu': instructor.tipo_vincu,
            'fichas': [{'id': f.id, 'num': f.num} for f in fichas],
        }
        return JsonResponse (data)
    return JsonResponse({'status': 'error', 'message': 'Instructor no encontrado'}, status=404)

@login_required
def editar_instructor(request, instructor_id):
    instructor = get_object_or_404(T_instru, pk=instructor_id)
    perfil = get_object_or_404(T_perfil, pk=instructor.perfil.id)

    if request.method == 'POST':
        form_perfil = PerfilForm(request.POST, instance=perfil)
        form_instructor = InstructorForm(request.POST, instance=instructor)

        if form_perfil.is_valid() and form_instructor.is_valid():
            ficha_ids = request.POST.getlist('ficha_id')
            nuevas_fichas = T_ficha.objects.filter(id__in=ficha_ids)

            for ficha in nuevas_fichas:
                if ficha.instru and ficha.instru.id != instructor.id:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'La ficha {ficha.num} ya tiene un instructor asignado: {ficha.instru.perfil.nom} {ficha.instru.perfil.apelli}'
                    }, status=409)

            fichas_actuales = T_ficha.objects.filter(instru=instructor)
            for ficha in fichas_actuales:
                if str(ficha.id) not in ficha_ids:
                    ficha.instru = None
                    ficha.save()

            for ficha in nuevas_fichas:
                ficha.instru = instructor
                ficha.save()

            form_perfil.save()
            form_instructor.save()

            return JsonResponse({'status': 'success', 'message': 'Instructor actualizado con éxito.'})
        else:
            errors = {
                'perfil': form_perfil.errors,
                'admin': form_instructor.errors
            }
            return JsonResponse({
                'status': 'error',
                'message': 'Error al actualizar el instructor',
                'errors': errors
            }, status=400)

    return JsonResponse({
        'status': 'error',
        'message': 'Método no permitido',
    }, status=405)

# Función auxiliar para formatear errores por fila
def formatear_error_csv(fila, errores_campos):
    fila_str = '\n  '.join([f"{k}: '{v}'" for k, v in fila.items()])
    return (
        "⚠️ Error de validación en una fila del archivo CSV:\n"
        "----------------------------------------\n"
        f"Datos de la fila:\n  {fila_str}\n\n"
        f"Errores encontrados:\n" + '\n'.join(errores_campos) + "\n"
        "----------------------------------------"
    )

def validar_formato_csv_basico(contenido_csv, campos_esperados):
    errores = []
    reader = csv.reader(StringIO(contenido_csv), delimiter=';')
    for i, row in enumerate(reader, start=1):
        if len(row) != len(campos_esperados):
            errores.append(
                f"Línea {i}: se esperaban {len(campos_esperados)} columnas, pero se encontraron {len(row)}. Contenido: {row}"
            )
    return errores
@login_required
def cargar_instructores_masivo(request):
    if request.method == 'POST':
        errores = []
        resumen = {
            "insertados": 0,
            "errores": 0,
            "duplicados_dni": []
        }
        MAX_FILAS = 100
        form = CargarInstructoresMasivoForm(request.POST, request.FILES)

        if form.is_valid():
            archivo = request.FILES['archivo']
            if not (archivo.name.lower().endswith('.csv') and archivo.content_type in ['text/csv', 'application/csv', 'text/plain']):
                errores.append(formatear_error_csv({}, ["Tipo de archivo no válido. Solo se permiten archivos CSV (.csv)"]))
                resumen["errores"] += 1
                return render(request, 'instructor_masivo_crear.html', {'form': form, 'errores': errores, 'resumen': resumen})

            datos_csv = TextIOWrapper(archivo.file, encoding='utf-8-sig')
            contenido_csv = datos_csv.read()

            if not contenido_csv.strip():
                errores.append(formatear_error_csv({}, ["El archivo está vacío."]))
                resumen["errores"] += 1
                return render(request, 'instructor_masivo_crear.html', {'form': form, 'errores': errores, 'resumen': resumen})

            CAMPOS_ESPERADOS = [
                'email', 'nom', 'apelli', 'tipo_dni', 'dni', 'tele',
                'dire', 'gene', 'fecha_naci', 'contra',
                'fecha_ini', 'fecha_fin', 'profe', 'tipo_vincu'
            ]

            errores_formato = validar_formato_csv_basico(contenido_csv, CAMPOS_ESPERADOS)
            if errores_formato:
                for e in errores_formato:
                    errores.append(formatear_error_csv({}, [e]))
                    resumen["errores"] += 1
                messages.warning(request, "El archivo tiene filas mal formateadas. No se insertó ningún registro.")
                return render(request, 'instructor_masivo_crear.html', {'form': form, 'errores': errores, 'resumen': resumen})

            try:
                filas_crudas = list(csv.DictReader(StringIO(contenido_csv), delimiter=';'))
            except Exception as e:
                errores.append(formatear_error_csv({}, [f"Error al leer el archivo CSV: {e}"]))
                resumen["errores"] += 1
                return render(request, 'instructor_masivo_crear.html', {'form': form, 'errores': errores, 'resumen': resumen})

            if not filas_crudas or not all(filas_crudas[0].keys()):
                errores.append(formatear_error_csv({}, [
                    "El archivo no tiene una fila de encabezado válida.",
                    "Verifique si el delimitador es ';' y que el archivo tenga encabezados correctos."
                ]))
                resumen["errores"] += 1
                return render(request, 'instructor_masivo_crear.html', {'form': form, 'errores': errores, 'resumen': resumen})

            campos_csv = [campo.strip().lower() for campo in filas_crudas[0].keys()]
            esperados = [campo.strip().lower() for campo in CAMPOS_ESPERADOS]

            if set(campos_csv) != set(esperados):
                errores.append(formatear_error_csv({}, [
                    "El encabezado del archivo no coincide con el formato esperado.",
                    f"Encabezado recibido: {campos_csv}",
                    f"Encabezado esperado: {esperados}"
                ]))
                resumen["errores"] += 1
                messages.warning(request, "El archivo no tiene un encabezado válido.")
                return render(request, 'instructor_masivo_crear.html', {'form': form, 'errores': errores, 'resumen': resumen})

            filas = [f for f in filas_crudas if any(valor.strip() for valor in f.values())]

            if len(filas) > MAX_FILAS:
                errores.append(formatear_error_csv({}, [f"El archivo tiene {len(filas)} filas, pero el máximo permitido es {MAX_FILAS}."]))
                resumen["errores"] += 1
                return render(request, 'instructor_masivo_crear.html', {'form': form, 'errores': errores, 'resumen': resumen})

            dnis_vistos = set()
            emails_vistos = set()

            for fila in filas:
                dni = fila.get('dni')
                email = fila.get('email')
                fila_errores = []

                if dni in dnis_vistos:
                    fila_errores.append(f"DNI duplicado en el archivo: {dni}")
                else:
                    dnis_vistos.add(dni)

                if email in emails_vistos:
                    fila_errores.append(f"Email duplicado en el archivo: {email}")
                else:
                    emails_vistos.add(email)

                if fila_errores:
                    errores.append(formatear_error_csv(fila, fila_errores))
                    resumen["errores"] += 1

            for fila in filas:
                try:
                    for campo in ['email', 'nom', 'apelli', 'tipo_dni', 'dni', 'tele', 'dire', 'gene', 'fecha_naci', 'profe', 'tipo_vincu']:
                        if not fila.get(campo, '').strip():
                            raise ValidationError(f"Campo requerido faltante: '{campo}'")

                    dni = fila['dni']
                    if T_perfil.objects.filter(dni=dni).exists():
                        resumen["duplicados_dni"].append(dni)
                        raise ValidationError(f"DNI duplicado en el sistema: {dni}")

                    validate_email(fila['email'].strip())
                    if T_perfil.objects.filter(mail=fila['email']).exists():
                        raise ValidationError(f"Email ya existe en el sistema: {fila['email']}")

                    datetime.strptime(fila['fecha_naci'].strip(), '%d/%m/%Y')
                    if fila.get('fecha_ini', '').strip():
                        datetime.strptime(fila['fecha_ini'].strip(), '%d/%m/%Y')
                    if fila.get('fecha_fin', '').strip():
                        datetime.strptime(fila['fecha_fin'].strip(), '%d/%m/%Y')

                except Exception as e:
                    resumen["errores"] += 1
                    errores.append(formatear_error_csv(fila, [force_str(e)]))

            if resumen["errores"] > 0:
                messages.warning(request, f"{resumen['errores']} errores encontrados. No se insertó ningún registro.")
                return render(request, 'instructor_masivo_crear.html', {'form': form, 'errores': errores, 'resumen': resumen})

            try:
                with transaction.atomic():
                    for fila in filas:
                        dni = fila['dni']
                        fecha_naci = datetime.strptime(fila['fecha_naci'].strip(), '%d/%m/%Y').date()
                        fecha_ini = datetime.strptime(fila['fecha_ini'].strip(), '%d/%m/%Y').date() if fila.get('fecha_ini', '').strip() else None
                        fecha_fin = datetime.strptime(fila['fecha_fin'].strip(), '%d/%m/%Y').date() if fila.get('fecha_fin', '').strip() else None

                        base_username = ''.join(c for c in unicodedata.normalize('NFKD', fila['nom'][:3] + fila['apelli'][:3]) if c.isalnum()).lower()
                        username = base_username
                        i = 1
                        while User.objects.filter(username=username).exists():
                            username = f"{base_username}{i}"
                            i += 1

                        user = User.objects.create_user(username=username, password=str(dni), email=fila['email'])

                        perfil = T_perfil(
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
                            rol="instructor"
                        )
                        perfil.full_clean()
                        perfil.save()

                        instructor = T_instru(
                            perfil=perfil,
                            esta="activo",
                            contra=fila.get('contra', ''),
                            profe=fila['profe'],
                            tipo_vincu=fila['tipo_vincu'],
                            fecha_ini=fecha_ini,
                            fecha_fin=fecha_fin
                        )
                        instructor.full_clean()
                        instructor.save()

                        resumen["insertados"] += 1

                messages.success(request, f"Se insertaron correctamente {resumen['insertados']} instructores.")

            except ValidationError as e:
                resumen["errores"] += 1
                resumen["insertados"] = 0
                errores.append(formatear_error_csv(fila, [force_str(e)]))
            except Exception as e:
                resumen["errores"] += 1
                resumen["insertados"] = 0
                errores.append(formatear_error_csv(fila, [force_str(e)]))

            return render(request, 'instructor_masivo_crear.html', {'form': form, 'errores': errores, 'resumen': resumen})

    else:
        form = CargarInstructoresMasivoForm()

    return render(request, 'instructor_masivo_crear.html', {'form': form})

### CUENTAS ###

@login_required
def cuentas(request):
    cuentas = T_cuentas.objects.all()
    return render(request, 'cuentas.html', {
        'cuentas': cuentas
    })

@login_required
def crear_pcuentas(request):
    if request.method == 'GET':
        user_form = UserFormCreate()
        perfil_form = PerfilForm()

        return render(request, 'cuentas_crear.html', {
            'user_form': user_form,
            'perfil_form': perfil_form,
        })
    else:
        try:
            user_form = UserFormCreate(request.POST)
            perfil_form = PerfilForm(request.POST)

            if user_form.is_valid() and perfil_form.is_valid():
                username = user_form.cleaned_data['username']
                if User.objects.filter(username=username).exists():
                    return render(request, 'cuentas_crear.html', {
                        'user_form': user_form,
                        'perfil_form': perfil_form,
                        'error1': 'El usuario ya existe.'
                    })

                # Creación del usuario
                new_user = user_form.save(commit=False)
                new_user.set_password(user_form.cleaned_data['password'])
                new_user.save()

                # Creación del perfil
                new_perfil = perfil_form.save(commit=False)
                new_perfil.user = new_user
                new_perfil.rol = 'cuentas'
                new_perfil.mail = new_user.email
                new_perfil.save()

                # Creación del gestor
                new_cuentas = T_cuentas(
                    perfil = new_perfil,
                    esta = 'activo'
                )
                new_cuentas.save()

                return redirect('cuentas')

            else:
                return render(request, 'cuentas_crear.html', {
                    'user_form': user_form,
                    'perfil_form': perfil_form,
                    'error': 'Por favor corrige los errores en el formulario.'
                })

        except ValueError as e:
            return render(request, 'cuentas_crear.html', {
                'user_form': user_form,
                'perfil_form': perfil_form,
                'error': f'Error: {str(e)}'
            })

@login_required
def cuentas_detalle(request, cuentas_id):
    cuentas = get_object_or_404(T_cuentas, pk=cuentas_id)
    perfil = cuentas.perfil
    if request.method == 'GET':
        perfil_form = PerfilEditForm(instance=perfil)
        return render(request, 'cuentas_detalle.html', {
            'cuentas': cuentas,
            'perfil_form': perfil_form,
        })
    elif request.method == 'POST':
        perfil_form = PerfilEditForm(request.POST, instance=perfil)
        if perfil_form.is_valid() :
            perfil_form.save()
            return redirect('cuentas')
        return render(request, 'cuentas_detalle.html', {
            'cuentas': cuentas,
            'perfil_form': perfil_form,
        })

### APRENDICES ###

@login_required
def aprendices(request):
    perfil = getattr(request.user, 't_perfil', None)
    rol = perfil.rol
    aprendices = T_apre.objects.select_related('perfil__user').all()

    perfil_form_data = request.session.pop('perfil_form_data', None)
    representante_form_data = request.session.pop('representante_form_data', None)

    perfil_form = PerfilForm(perfil_form_data, prefix='perfil') if perfil_form_data else PerfilForm(prefix='perfil')
    representante_form = RepresanteLegalForm(representante_form_data, prefix='representante') if representante_form_data else RepresanteLegalForm(prefix='representante')


    return render(request, 'aprendiz.html', {
        'aprendices': aprendices,
        'rol': rol,
        'perfil_form': perfil_form,
        'representante_form': representante_form
    })

## Endpoint para editar aprendiz ##
@login_required
def obtener_aprendiz(request, aprendiz_id):
    aprendiz = T_apre.objects.filter(id=aprendiz_id).first()
    perfil = T_perfil.objects.filter(id=aprendiz.perfil_id).first()
    representante = T_repre_legal.objects.filter(id=aprendiz.repre_legal_id).first()
    if aprendiz and perfil:
        data = {
            'perfil-nom': perfil.nom,
            'perfil-apelli': perfil.apelli,
            'perfil-tipo_dni': perfil.tipo_dni,
            'perfil-dni': perfil.dni,
            'perfil-tele': perfil.tele,
            'perfil-dire': perfil.dire,
            'perfil-mail': perfil.mail,
            'perfil-gene': perfil.gene,
            'perfil-fecha_naci': perfil.fecha_naci,
            'representante-nom': representante.nom,
            'representante-dni': representante.dni,
            'representante-tele': representante.tele,
            'representante-dire': representante.dire,
            'representante-mail': representante.mail,
            'representante-paren': representante.paren
        }
        return JsonResponse(data)
    return JsonResponse({'error': 'Aprendiz no encontrado'}, status=404)

# Enviar datos a los filtros de aprendices:

## Filtro de usuario creacion ##
@login_required
def obtener_usuarios_creacion(request):
    usuarios_ids = T_apre.objects.values_list('usu_crea', flat=True,).distinct()

    # Obtener los perfiles relacionados a esos usuarios
    perfiles = T_perfil.objects.filter(user__id__in=usuarios_ids).values('nom', 'apelli').distinct()

    # Formatear como "Nombre Apellido"
    usuarios = [f"{perfil['nom']} {perfil['apelli']}" for perfil in perfiles]

    return JsonResponse(usuarios, safe=False)

@login_required
def obtener_opciones_estados(request):
    estados = T_apre.objects.values_list('esta', flat=True).distinct()
    return JsonResponse(list(estados), safe=False)

## Endpoint para filtrar aprendices en la tabla ##

@login_required
def filtrar_aprendices(request):
    if request.user.is_authenticated:
        logger.warning(f"Usuario autenticado:{request.user}")
    else:
        logger.warning("Usuario anónimo")
    usuarios = request.GET.getlist('usuario_creacion', [])
    estado = request.GET.getlist('estado', [])
    fecha = request.GET.get('fecha_creacion_', None)
    ordenar = request.GET.get('ordenar_por', None)

    aprendices = T_apre.objects.all()

    if usuarios:
        filtros = Q()

        for usuario in usuarios:
            nombre, *apellido = usuario.split(" ")
            apellido = " ".join(apellido)

            filtros |= Q(usu_crea__t_perfil__nom__icontains=nombre, usu_crea__t_perfil__apelli__icontains=apellido)
        
        aprendices = aprendices.filter(filtros)
        
    if estado:
        aprendices = aprendices.filter(esta__in=estado)

    if fecha:
        # Convertir la fecha recibida en el formato adecuado
        fecha_creacion = datetime.strptime(fecha, '%Y-%m-%d').date()

        # Convertir la fecha de 'date_joined' a solo la fecha sin la hora
        aprendices = aprendices.annotate(fecha_sin_hora=Cast('perfil__user__date_joined', output_field=DateField()))

        # Filtrar por la fecha truncada
        aprendices = aprendices.filter(fecha_sin_hora=fecha_creacion)

    if ordenar:
        if ordenar == 'fecha_desc':
            aprendices = aprendices.order_by('-perfil__user__date_joined')
        elif ordenar == 'fecha_asc':
            aprendices = aprendices.order_by('perfil__user__date_joined')

    resultados = [
        {
            'id': a.id,
            'nombre': a.perfil.nom,
            'apellido': a.perfil.apelli,
            'telefono': a.perfil.tele,
            'direccion': a.perfil.dire,
            'mail': a.perfil.mail,
            'fecha_naci': a.perfil.fecha_naci,
            'estado': a.esta,
            'dni': a.perfil.dni,
        }
        for a in aprendices
    ]
    return JsonResponse(resultados, safe=False)

@login_required
def ver_perfil_aprendiz(request, aprendiz_id):
    aprendiz = get_object_or_404(T_apre, id=aprendiz_id)
    repre_legal = get_object_or_404(T_repre_legal, id=aprendiz.repre_legal.id)
    gestor = None
    if aprendiz.grupo:
        try:
            gestor = T_perfil.objects.get(user=aprendiz.grupo.autor)
        except T_perfil.DoesNotExist:
            gestor = None 
    return render(request, 'aprendiz_perfil_modal.html', {
        'aprendiz': aprendiz,
        'repre_legal': repre_legal,
        'gestor': gestor
        })

@login_required
def crear_aprendices(request):
    if request.method == 'POST':
        perfil_form = PerfilForm(request.POST, prefix='perfil')
        representante_form = RepresanteLegalForm(request.POST, prefix='representante')

        if perfil_form.is_valid() and representante_form.is_valid():
            try:
                dni = perfil_form.cleaned_data['dni']
                if T_perfil.objects.filter(dni=dni).exists():
                    raise ValueError("El número de documento ya está registrado en el sistema.")

                fecha_nacimiento = perfil_form.cleaned_data['fecha_naci']
                if fecha_nacimiento:
                    edad = (timezone.now().date() - fecha_nacimiento).days // 365
                    if edad < 14:
                        raise ValueError("El aprendiz debe tener al menos 14 años para registrarse.")
                else:
                    raise ValueError("La fecha de nacimiento es obligatoria.")

                nombre = perfil_form.cleaned_data['nom']
                apellido = perfil_form.cleaned_data['apelli']
                base_username = (nombre[:3] + apellido[:3]).lower()
                username = base_username
                i = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{i}"
                    i += 1

                # contraseña = generar_contraseña()

                new_user = User.objects.create_user(
                    username=username,
                    password=str(dni),
                    email=perfil_form.cleaned_data['mail']
                )

                new_perfil = perfil_form.save(commit=False)
                new_perfil.user = new_user
                new_perfil.rol = 'aprendiz'
                new_perfil.mail = new_user.email
                new_perfil.save()

                nombre_repre = representante_form.cleaned_data['nom']
                telefono_repre = representante_form.cleaned_data['tele']
                new_repre_legal = T_repre_legal.objects.filter(
                    nom=nombre_repre,
                    tele=telefono_repre
                ).first()

                if not new_repre_legal:
                    new_repre_legal = representante_form.save()
                
                perfil = getattr(request.user, 't_perfil', None)

                T_apre.objects.create(
                    cod="z",
                    esta="Activo",
                    perfil=new_perfil,
                    repre_legal=new_repre_legal,
                    usu_crea = perfil.user
                )

                return redirect('aprendices')

            except ValueError as e:
                messages.error(request, f'Ocurrió un error: {str(e)}')
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')

        # Redirigir de nuevo a la vista principal con los errores y formularios
        aprendices_url = reverse('aprendices')
        query_params = '?modal=open'  # Parámetro para abrir el modal automáticamente
        response = redirect(f'{aprendices_url}{query_params}')
        request.session['perfil_form_data'] = request.POST
        request.session['representante_form_data'] = request.POST
        return response

    return redirect('aprendices')

@login_required
def editar_aprendiz(request, id):
    aprendiz = get_object_or_404(T_apre, pk=id)
    perfil = get_object_or_404(T_perfil, pk=aprendiz.perfil_id)
    representante = get_object_or_404(T_repre_legal, pk=aprendiz.repre_legal_id)
    
    if request.method == 'POST':
        form_perfil = PerfilForm(request.POST, instance=perfil, prefix='perfil')
        form_repre = RepresanteLegalForm(request.POST, instance=representante, prefix='representante')
        
        if form_perfil.is_valid() and form_repre.is_valid():
            form_perfil.save()
            form_repre.save()
            return JsonResponse({'success': True, 'message': 'Aprendiz actualizado con exito.'})
        else:
            errores = {
                'perfil': form_perfil.errors,
                'representante': RepresanteLegalForm.errors
            }
            return JsonResponse({'success': False, 'message': 'Error al actualizar el aprendiz', 'errors': errores}, status=400) 
    
    return JsonResponse({'success': False, 'message': 'Método no permitido.'}, status=405)

@login_required
def eliminar_aprendiz(request, aprendiz_id):  # funcion para eliminar aprendiz

    aprendiz = get_object_or_404(T_apre, pk=aprendiz_id)

    if request.method == 'POST':
        aprendiz.delete()
        return redirect('aprendices')
    return render(request, '', {'aprendiz': aprendiz})

### LIDERES ###

@login_required
def lideres(request):
    lideres = T_lider.objects.select_related('perfil__user').all()
    perfil_form = PerfilForm()
    return render(request, 'lideres.html', {
        'lideres': lideres,
        'perfil_form': perfil_form,
    })

@login_required  # Funcion para crear lider
def crear_lider(request):
    if request.method == 'POST':
        perfil_form = PerfilForm(request.POST)

        if perfil_form.is_valid():
            dni = perfil_form.cleaned_data.get('dni')
            email = perfil_form.cleaned_data.get('mail')
            if T_perfil.objects.filter(dni__iexact = dni).exists():
                return JsonResponse({'status': 'error', 'message': 'Ya existe un usuario con ese DNI'}, status = 400)
            
            if T_perfil.objects.filter(mail__iexact = email).exists():
                return JsonResponse({'status': 'error', 'message': 'Ya existe un usuario con ese email'}, status = 400)
        
            nombre = perfil_form.cleaned_data['nom']
            apellido = perfil_form.cleaned_data['apelli']
            base_username = (nombre[:3] + apellido[:3]).lower()
            username = base_username
            i = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{i}"
                i += 1

            # contraseña = generar_contraseña()

            new_user = User.objects.create_user(
                username=username,
                password=str(dni),
                email=perfil_form.cleaned_data['mail']
            )

            new_perfil = perfil_form.save(commit=False)
            new_perfil.user = new_user
            new_perfil.rol = 'lider'
            new_perfil.mail = new_user.email
            new_perfil.save()
                    
            new_lider = T_lider.objects.create(
                area = "Equipo Nacional",
                esta = "Activo",
                perfil = new_perfil
            )
            return JsonResponse({'status': 'success', 'message': 'Lider creado con exito.'})
        else:
            errores_dict = {perfil_form.errors.get_json_data()}
            errores_custom = []

            for field, errors_list in errores_dict.items():
                # Obtiene el label personalizado del campo
                nombre_campo = perfil_form.fields[field].label or field.capitalize()
                
                for err in errors_list:
                    mensaje = f"{nombre_campo}: {err['message']}"
                    errores_custom.append(mensaje)

            return JsonResponse({'status': 'error', 'message':'Errores en el formulario', 'errors': '<br>'.join(errores_custom)}, status = 400)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

@login_required  # Funcion para actualizar informacion de lider
def obtener_lider(request, lider_id):
    lider = T_lider.objects.filter(id=lider_id).first()

    if lider:
        data = {
            'lider-nom': lider.perfil.nom,
            'lider-apelli': lider.perfil.apelli,
            'lider-tipo_dni': lider.perfil.tipo_dni,
            'lider-dni': lider.perfil.dni,
            'lider-tele': lider.perfil.tele,
            'lider-dire': lider.perfil.dire,
            'lider-mail': lider.perfil.mail,
            'lider-gene': lider.perfil.gene,
            'lider-fecha_naci': lider.perfil.fecha_naci,
        }
        return JsonResponse (data)
    return JsonResponse({'status': 'error', 'message': 'Lider no encontrado'}, status=404)

@login_required
def editar_lider(request, lider_id):
    lider = get_object_or_404(T_lider, pk=lider_id)
    perfil = get_object_or_404(T_perfil, pk = lider.perfil.id)

    if request.method == 'POST':
        form_perfil = PerfilForm(request.POST, instance=perfil)

        if form_perfil.is_valid():
            form_perfil.save()
            return JsonResponse({'status': 'success', 'message': 'Lider actualizado con exito.'})
        else:
            errors = {
                'perfil': form_perfil.errors,
            }
            return JsonResponse({'status': 'error', 'message': 'Error al actualizar el lider', 'errors': errors}, status = 400)
    return JsonResponse({'status': 'error', 'message': 'Metodo no permitido', 'errors': errors}, status = 405)

@login_required
def eliminar_lider(request, lider_id):
    lider = get_object_or_404(T_lider, id=lider_id)
    if request.method == 'POST':
        perfil = lider.perfil
        usuario = perfil.user
        
        lider.delete()
        perfil.delete()
        usuario.delete()

        return JsonResponse({'status': 'success', 'message': 'Lider eliminado correctamente.'}, status=200)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)


### ADMINISTRADOR ###


@login_required
def administradores(request):
    administradores = T_admin.objects.select_related('perfil__user').all()
    perfil_form = PerfilForm()
    admin_form = AdministradoresForm()
    return render(request, 'administradores.html', {
        'administradores': administradores,
        'perfil_form': perfil_form,
        'admin_form': admin_form
    })

@login_required
def crear_administrador(request):
    if request.method == 'POST':
        perfil_form = PerfilForm(request.POST)
        admin_form = AdministradoresForm(request.POST)

        if perfil_form.is_valid() and admin_form.is_valid():
            dni = perfil_form.cleaned_data.get('dni')
            email = perfil_form.cleaned_data.get('mail')
            if T_perfil.objects.filter(dni__iexact = dni).exists():
                return JsonResponse({'status': 'error', 'message': 'Ya existe un usuario con ese DNI'}, status = 400)
            
            if T_perfil.objects.filter(mail__iexact = email).exists():
                return JsonResponse({'status': 'error', 'message': 'Ya existe un usuario con ese email'}, status = 400)
        
            nombre = perfil_form.cleaned_data['nom']
            apellido = perfil_form.cleaned_data['apelli']
            base_username = (nombre[:3] + apellido[:3]).lower()
            username = base_username
            i = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{i}"
                i += 1

            # contraseña = generar_contraseña()

            new_user = User.objects.create_user(
                username=username,
                password=str(dni),
                email=perfil_form.cleaned_data['mail']
            )

            new_perfil = perfil_form.save(commit=False)
            new_perfil.user = new_user
            new_perfil.rol = 'admin'
            new_perfil.mail = new_user.email
            new_perfil.save()
            
            perfil = getattr(request.user, 't_perfil', None)
        
            new_admin = admin_form.save(commit=False)
            new_admin.perfil = new_perfil
            new_admin.esta = "Activo"
            new_admin.save()
            return JsonResponse({'status': 'success', 'message': 'Administrador creado con exito.'})
        else:
            errores_dict = {**perfil_form.errors.get_json_data(), **admin_form.errors.get_json_data()}
            errores_custom = []

            for field, errors_list in errores_dict.items():
                nombre_campo = (perfil_form.fields.get(field) or admin_form.fields.get(field)).label or field.capitalize()
                
                for err in errors_list:
                    mensaje = f"{nombre_campo}: {err['message']}"
                    errores_custom.append(mensaje)

            return JsonResponse({
                'status': 'error',
                'message': 'Errores en el formulario',
                'errors': '<br>'.join(errores_custom)
            }, status=400)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)


@login_required
def obtener_administrador(request, admin_id):
    administrador = T_admin.objects.filter(id=admin_id).first()

    if administrador:
        data = {
            'admin-nom': administrador.perfil.nom,
            'admin-apelli': administrador.perfil.apelli,
            'admin-tipo_dni': administrador.perfil.tipo_dni,
            'admin-dni': administrador.perfil.dni,
            'admin-tele': administrador.perfil.tele,
            'admin-dire': administrador.perfil.dire,
            'admin-mail': administrador.perfil.mail,
            'admin-gene': administrador.perfil.gene,
            'admin-fecha_naci': administrador.perfil.fecha_naci,
            'admin-area': administrador.area
        }
        return JsonResponse (data)
    return JsonResponse({'status': 'error', 'message': 'Admin no encontrado'}, status=404)

@login_required
def eliminar_administrador(request, admin_id):
    admin = get_object_or_404(T_admin, pk=admin_id)

    if request.method == 'POST':
        perfil = admin.perfil
        usuario = perfil.user

        admin.delete()
        perfil.delete()
        usuario.delete()

        return JsonResponse({'status': 'success', 'message': 'Administrador eliminado correctamente.'}, status=200)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)

@login_required
def editar_administrador(request, admin_id):
    administrador = get_object_or_404(T_admin, pk=admin_id)
    perfil = get_object_or_404(T_perfil, pk = administrador.perfil.id)

    if request.method == 'POST':
        form_perfil = PerfilForm(request.POST, instance=perfil)
        form_administrador  = AdministradoresForm(request.POST, instance = administrador)

        if form_perfil.is_valid() and form_administrador.is_valid():
            form_perfil.save()
            form_administrador.save()
            return JsonResponse({'status': 'success', 'message': 'Administrador actualizado con exito.'})
        else:
            errors = {
                'perfil': form_perfil.errors,
                'admin': form_administrador.errors
            }
            return JsonResponse({'status': 'error', 'message': 'Error al actualizar el aprendiz', 'errors': errors}, status = 400)
    return JsonResponse({'status': 'error', 'message': 'Metodo no permitido', 'errors': errors}, status = 405)

### NOVEDADES ###

@login_required
def novedades(request):
    novedades = T_nove.objects.all()
    return render(request, 'novedades.html', {
        'novedades': novedades
    })

@login_required
def crear_novedad(request):

    if request.method == 'GET':

        novedad_form = NovedadForm()

        return render(request, 'novedad_crear.html', {
            'novedad_form': novedad_form
        })
    else:
        try:
            novedad_form = NovedadForm(request.POST)
            if novedad_form.is_valid():
                # Creacion de la novedad
                new_novedad = novedad_form.save(commit=False)
                new_novedad.estado = 'creado'
                new_novedad.save()
                return redirect('novedades')

        except ValueError as e:
            return render(request, 'novedad_crear.html', {
                'novedad_form': novedad_form,
                'error': f'Ocurrió un error: {str(e)}'
            })

## DEPARTAMENTOS ##

@login_required
def departamentos(request):
    departamentos = T_departa.objects.all()
    return render(request, 'departamentos.html', {
        'departamentos': departamentos
    })

@login_required
def creardepartamentos(request):  # funcion para crear departamento
    if request.method == 'GET':
        departamentosForm = DepartamentoForm()
        return render(request, 'departamentos_crear.html', {
            'departamentosForm': departamentosForm
        })
    else:
        try:
            departamentosForm = DepartamentoForm(request.POST)
            if departamentosForm.is_valid():
                new_departamento = departamentosForm.save(commit=False)
                new_departamento.save()
                return redirect('departamentos')
        except ValueError:
            return render(request, 'departamentos_crear.html', {
                'departamentosForm': departamentosForm,
                'error': '"Error al crear departamento. Verifique los datos.'
            })

@login_required
# funcion para actualizar info departamento
def detalle_departamentos(request, departamento_id):
    departamentos = get_object_or_404(T_departa, id=departamento_id)
    if request.method == 'GET':
        departamentosForm = DepartamentoForm(instance=departamentos)
        return render(request, 'departamentos_detalle.html', {
            'departamentos': departamentos,
            'departamentosForm': departamentosForm
        })
    else:
        try:
            departamentosForm = DepartamentoForm(
                request.POST, instance=departamentos)
            if departamentosForm.is_valid():
                departamentosForm.save()
                return redirect('departamentos')
        except ValueError:
            return render(request, 'departamentos_detalle.html', {
                'departamentosForm': departamentosForm,
                'error': '"Error al actualizar departamento. Verifique los datos.'
            })

@login_required
def eliminar_departamentos(request, departamento_id):
    departamento = get_object_or_404(T_departa, id=departamento_id)
    if request.method == 'POST':
        departamento.delete()
        return redirect('departamentos')
    return render(request, 'confirmar_eliminacion_departamento.html', {
        'departamento': departamento,
    })

## MUNICIPIOS ##

@login_required
def municipios(request):
    municipios = T_munici.objects.all()
    return render(request, 'municipios.html', {
        'municipios': municipios
    })

@login_required
def crearmunicipios(request):  # funcion para crear municipio
    if request.method == 'GET':
        municipiosForm = MunicipioForm()
        return render(request, 'municipios_crear.html', {
            'municipiosForm': municipiosForm
        })
    else:
        try:
            municipiosForm = MunicipioForm(request.POST)
            if municipiosForm.is_valid():
                new_municipio = municipiosForm.save(commit=False)
                new_municipio.save()
                return redirect('municipios')
        except ValueError:
            return render(request, 'municipios_crear.html', {
                'municipiosForm': municipiosForm,
                'error': 'Error al al crear municipio. Verifique los datos.'
            })


@login_required
def detalle_municipios(request, municipio_id):  # funcion para editar municipio
    municipios = get_object_or_404(T_munici, id=municipio_id)

    if request.method == 'GET':
        municipiosForm = MunicipioForm(instance=municipios)
        return render(request, 'municipios_detalle.html', {
            'municipios': municipios,
            'municipiosForm': municipiosForm
        })
    else:
        try:
            municipiosForm = MunicipioForm(request.POST, instance=municipios)
            if municipiosForm.is_valid():
                municipiosForm.save()
                return redirect('municipios')
        except ValueError:
            return render(request, 'municipios_detalle.html', {
                'municipiosForm': municipiosForm,
                'error': 'Error al actualizar. Verifique los datos.'
            })

@login_required
def eliminar_municipios(request, municipio_id):  # funcion para eliminar municipio
    municipio = get_object_or_404(T_munici, id=municipio_id)

    if request.method == 'POST':
        municipio.delete()
        return redirect('municipios')
    return render(request, 'confirmar_eliminacion_municipio.html', {
        'municipio': municipio,
    })

## Instituciones ##

@login_required
def instituciones(request):
    instituciones = T_insti_edu.objects.all()
    institucionForm = InstitucionForm()

    return render(request, 'instituciones.html', {
        'instituciones': instituciones,
        'institucionForm': institucionForm
    })

## Endpoint para editar institucion ##
@login_required
def obtener_institucion(request, institucion_id):
    institucion = T_insti_edu.objects.filter(id=institucion_id).first()
    if institucion:
        data = {
            'nom': institucion.nom,
            'dire': institucion.dire,
            'municipio': institucion.muni.id,
            'secto': institucion.secto,
            'coordi': institucion.coordi,
            'coordi_mail': institucion.coordi_mail,
            'coordi_tele': institucion.coordi_tele,
            'esta': institucion.esta,
            'insti_mail': institucion.insti_mail,
            'recto': institucion.recto,
            'recto_tel': institucion.recto_tel,
            'vigen': institucion.vigen,
            'cale': institucion.cale,
            'dane': institucion.dane,
            'gene': institucion.gene,
            'grados': institucion.grados,
            'jorna': institucion.jorna,
            'num_sedes': institucion.num_sedes,
            'zona': institucion.zona,
        }
        return JsonResponse(data)
    return JsonResponse({'error': 'Institución no encontrada'}, status=404)

@login_required
def api_municipios(request):
    municipios = T_munici.objects.all().values('id', 'nom_munici')
    data = list(municipios)
    return JsonResponse(data, safe=False)

@login_required
def crear_instituciones(request):
    if request.method == 'POST':
        try:
            institucionForm = InstitucionForm(request.POST)

            if institucionForm.is_valid():
                departamento_id = institucionForm.cleaned_data.get('depa')

                if departamento_id:
                    institucionForm.fields['muni'].queryset = T_munici.objects.filter(nom_departa=departamento_id)

                nombre = institucionForm.cleaned_data.get('nom')
                municipio = institucionForm.cleaned_data.get('muni')

                if T_insti_edu.objects.filter(nom = nombre, muni = municipio).exists():
                    errors = "<ul><li>Ya existe una institución con ese nombre asociada al municipio seleccionado.</li></ul>"
                    return JsonResponse({'status': 'error', 'message': 'Institución duplicada.', 'errors': errors}, status=400)

                new_institucion = institucionForm.save(commit=False)
                new_institucion.vigen = timezone.now().year
                new_institucion.save()

                return JsonResponse({'status':'success', 'message': 'Institución creada correctamente.'}, status=200)

            errors = institucionForm.errors.as_ul()
            return JsonResponse({'status': 'error','message': 'Valide el formulario nuevamente', 'errors': errors}, status=400)

        except ValueError as e:
            errors = "<ul><li>Error interno: {}</li></ul>".format(str(e))
            return JsonResponse({'status':'error','errors': errors}, status=500)

    else:
        return JsonResponse({"errors": "<ul><li>Método no permitido.</li></ul>"}, status=405)

@login_required
def editar_institucion(request, institucion_id):
    institucion = get_object_or_404(T_insti_edu, id = institucion_id)

    try:
        institucion.nom = request.POST.get('nom', '').strip()
        institucion.dire = request.POST.get('dire', '').strip()
        institucion.secto = request.POST.get('secto', '').strip()
        institucion.coordi = request.POST.get('coordi', '').strip()
        institucion.coordi_mail = request.POST.get('coordi_mail', '').strip()
        institucion.coordi_tele = request.POST.get('coordi_tele', '').strip()
        institucion.esta = request.POST.get('esta', '').strip()
        institucion.insti_mail = request.POST.get('insti_mail', '').strip()
        institucion.recto = request.POST.get('recto', '').strip()
        institucion.recto_tel = request.POST.get('recto_tel', '').strip()
        institucion.cale = request.POST.get('cale', '').strip()
        institucion.dane = request.POST.get('dane', '').strip()
        institucion.gene = request.POST.get('gene', '').strip()
        institucion.grados = request.POST.get('grados', '').strip()
        institucion.jorna = request.POST.get('jorna', '').strip()
        institucion.num_sedes = request.POST.get('num_sedes', '').strip()
        institucion.zona = request.POST.get('zona', '').strip()

        municipio_id = request.POST.get('muni')
        if municipio_id:
            institucion.muni_id = municipio_id

        institucion.save()
        return JsonResponse({'status': 'success', 'message': 'Institucion actualizada.'}, status = 200)
    except Exception as e:
        return JsonResponse({'status': 'false', 'message':'Error en la operacion', 'errors': str(e)}, status = 400)

@login_required  # funcion para eliminar institucion
def eliminar_instituciones(request, institucion_id):
    institucion = get_object_or_404(T_insti_edu, id=institucion_id)

    if request.method == 'POST':
        institucion.delete()
        return redirect('instituciones')
    return render(request, 'confirmar_eliminacion_instituciones.html', {
        'institucion': institucion,
    })

@login_required
def obtener_institucion_modal(request, institucion_id):
    institucion = get_object_or_404(T_insti_edu, id=institucion_id)
    return render(request, 'institucion_ver_modal.html', {
        'institucion': institucion
    })


## Centros de formacion ##
@login_required
def centrosformacion(request):
    if request.method == 'GET':
        centroformacionForm = CentroFormacionForm()
        return render(request, 'centro_formacion.html', {
            'centroformacionForm': centroformacionForm
        })
    else:
        return render(request, 'centro_formacion.html', {
            'centroformacionForm': centroformacionForm,
            })

# Funcion para crear centros de formacion
@login_required
def crear_centro(request):
    if request.method == 'POST':
        centroForm = CentroFormacionForm(request.POST)
        if centroForm.is_valid():
            nom = centroForm.cleaned_data.get('nom')
            cod = centroForm.cleaned_data.get('cod')

            if T_centro_forma.objects.filter(nom__iexact = nom).exists():
                return JsonResponse({'status': 'error', 'message': 'Ya existe un centro con ese nombre'}, status = 400)

            if T_centro_forma.objects.filter(cod__iexact = cod).exists():
                return JsonResponse({'status': 'error', 'message': 'Ya existe un centro con ese codigo'}, status = 400)

            centroForm.save()
            return JsonResponse({'status': 'success', 'message': 'Centro creado con exito.'}, status = 200)
        else:
            errores_dict = centroForm.errors.get_json_data()
            errores_custom = []

            for field, errors_list in errores_dict.items():
                # Obtiene el label personalizado del campo
                nombre_campo = centroForm.fields[field].label or field.capitalize()
                
                for err in errors_list:
                    mensaje = f"{nombre_campo}: {err['message']}"
                    errores_custom.append(mensaje)

            return JsonResponse({'status': 'error', 'message':'Errores en el formulario', 'errors': '<br>'.join(errores_custom)}, status = 400)
    return JsonResponse({'status': 'error', 'message': 'Metodo no permitido'}, status = 405)

## Endpoint para listar centro
@login_required
def listar_centros_formacion_json(request):
    centros = T_centro_forma.objects.all()
    data = []
    for centro in centros:
        data.append({
            'id': centro.id,
            'nom': centro.nom,
            'cod': centro.cod,
            'depa': centro.depa.nom_departa
        })
    return JsonResponse({'data': data})

## Endpoint para editar centro ##
@login_required
def obtener_centro(request, centro_id):
    centro = T_centro_forma.objects.filter(id=centro_id).first()
    
    if centro:
        data = {
            'centro-nom': centro.nom,
            'centro-depa': centro.depa.id,
            'centro-codi': centro.cod
        }
        return JsonResponse(data)
    return JsonResponse({'error': 'Centro no encontrado'}, status=404)

@login_required
def editar_centro(request, centro_id):
    centro = get_object_or_404(T_centro_forma, pk=centro_id)
    
    if request.method == 'POST':
        form_centro = CentroFormacionForm(request.POST, instance=centro)
        nom = request.POST.get('nom', '').strip()
        cod = request.POST.get('cod', '').strip()

        if T_centro_forma.objects.filter(nom__iexact=nom).exclude(pk=centro_id).exists():
            return JsonResponse({'status': 'error', 'message': 'Ya existe otro centro con este nombre.'}, status=400)

        if T_centro_forma.objects.filter(cod__iexact=cod).exclude(pk=centro_id).exists():
            return JsonResponse({'status': 'error', 'message': 'Ya existe otro centro con este código.'}, status=400)


        if form_centro.is_valid():
            form_centro.save()
            return JsonResponse({'status': 'success', 'message': 'Centro de Formacion actualizado con exito.'})
        else:
            errores = form_centro.errors
            return JsonResponse({'status': 'error', 'message': 'Error al actualizar el centro de formacion', 'errors': {'centro': errores}}, status=400) 
    
    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)

# Endpoiont para eliminar centro de formacion
@login_required  
def eliminar_centro(request, centro_id):
    if request.method == 'POST':
        try:
            centro = get_object_or_404(T_centro_forma, id=centro_id)
            centro.delete()
            return JsonResponse({'status': 'success', 'message': 'Centro eliminado con exito.'}, status = 200)
        except centro.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'No encontrado.'}, status = 404)       
    return JsonResponse({'status': 'error', 'message': 'Metodo no permitido.'}, status = 405)

@login_required
def obtener_municipios(request):
    departamento_id = request.GET.get('departamento_id')
    if departamento_id:
        municipios = T_munici.objects.filter(nom_departa_id=departamento_id).values('id', 'nom_munici')
        return JsonResponse(list(municipios), safe=False)
    return JsonResponse({'error': 'No se proporcionó el ID del departamento'}, status=400)

@login_required
def obtener_departamentos(request):
    departamentos = T_departa.objects.all().values('id', 'nom_departa') 
    return JsonResponse(list(departamentos), safe=False)

# Función para generar contraseña aleatoria
def generar_contraseña(length=8):
    caracteres = string.ascii_letters + string.digits
    return ''.join(random.choice(caracteres) for _ in range(length))

@login_required
def cargar_aprendices_masivo(request):
    if request.method == 'POST':

        errores = []
        resumen = {
            "insertados": 0,
            "errores": 0,
            "duplicados_dni": []
        }
        form = CargarAprendicesMasivoForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Iniciar una transacción
                with transaction.atomic():
                    archivo = request.FILES['archivo']
                    datos_csv = TextIOWrapper(archivo.file, encoding='utf-8-sig')

                    # Validar extensión del archivo
                    if not archivo.name.lower().endswith('.csv'):
                        messages.error(request, "Solo se permiten archivos CSV (.csv).")
                        resumen["errores"] += 1
                        errores.append(f"Solo se permiten archivos CSV (.csv)")
                        raise ValidationError(f"Solo se permiten archivos CSV (.csv).")
                    
                    # Validar tipo MIME (opcional pero recomendado)
                    allowed_mime_types = ['text/csv', 'application/csv', 'text/plain']
                    if archivo.content_type not in allowed_mime_types:
                        messages.error(request, "Tipo de archivo no válido (solo CSV).")
                        resumen["errores"] += 1
                        errores.append(f"Solo se permiten archivos CSV (.csv)")
                        raise ValidationError(f"Solo se permiten archivos CSV (.csv).")
                                
                    # Convertir punto y coma a coma en caso de que el CSV use el delimitador ";"
                    contenido_csv = datos_csv.read().replace(';', ',')

                    # Leer el archivo CSV
                    lector = csv.DictReader(contenido_csv.splitlines())

                    representantes = {}  # Diccionario para llevar un registro de los representantes procesados
                    perfil_crea = getattr(request.user, 't_perfil', None)

                    for fila in lector:
                        try:

                            # Validar campos obligatorios
                            campos_requeridos = ['email', 'nom', 'dni', 'apelli', 'tipo_dni', 'tele', 'dire', 'gene',
                            'nom_repre', 'dni_repre', 'tele_repre', 'dire_repre', 'mail_repre', 'parentezco', 'ciu', 'depa']
                            for campo in campos_requeridos:
                                if campo not in fila or not fila[campo].strip():
                                    raise ValidationError(f"Campo requerido faltante: '{campo}' en fila: {fila}")

                            
                            # Verificar si el DNI ya existe
                            dni = fila['dni']
                            if T_perfil.objects.filter(dni=dni).exists():
                                raise ValidationError(f"DNI duplicado: {dni}")

                            # Validar emails
                            validate_email(fila['email'])
                            validate_email(fila['mail_repre'])

                            # Convertir la fecha de nacimiento si existe
                            fecha_naci_str = fila.get('fecha_naci', '').strip()
                            if fecha_naci_str:
                                try:
                                    fecha_naci = datetime.strptime(fecha_naci_str, '%d/%m/%Y').date()
                                except ValueError as e:
                                    raise ValidationError(f"Formato de fecha inválido en fila {fila}: {str(e)}")  # Cambiar esto
                            else:
                                fecha_naci = None

                            # Generar un username único basado en el nombre y apellido
                            base_username = (fila['nom'][:3] + fila['apelli'][:3]).lower()  # Tomamos los primeros 3 caracteres del nombre y apellido
                            username = base_username
                            i = 1

                            # Verificar que el username no exista
                            while User.objects.filter(username=username).exists():
                                username = f"{base_username}{i}"
                                i += 1

                            # Generar contraseña aleatoria
                            # contraseña = generar_contraseña()

                            # Crear el usuario
                            user = User.objects.create_user(
                                username=username,
                                password=str(dni),
                                email=fila['email']
                            )
                            
                            # Crear el perfil
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
                                fecha_naci=fecha_naci,  # Asignar la fecha ya convertida
                                rol="aprendiz"
                            )

                            # Verificar si el representante legal ya existe
                            nombre_repre = fila['nom_repre']
                            telefono_repre = fila['tele_repre']
                            repre_legal = representantes.get((nombre_repre, telefono_repre))

                            if not repre_legal:
                                # Si no existe, buscar en la base de datos
                                repre_legal = T_repre_legal.objects.filter(
                                    nom=nombre_repre,
                                    tele=telefono_repre
                                ).first()

                                if not repre_legal:
                                    # Si no existe en la base de datos, crear uno nuevo
                                    repre_legal = T_repre_legal.objects.create(
                                        nom=nombre_repre,
                                        dni=fila['dni_repre'],
                                        tele=telefono_repre,
                                        dire=fila['dire_repre'],
                                        mail=fila['mail_repre'],
                                        paren=fila['parentezco']
                                    )
                                    
                                # Registrar el representante en el diccionario para evitar duplicados
                                representantes[(nombre_repre, telefono_repre)] = repre_legal

                            # Crear el aprendiz
                            aprendiz = T_apre.objects.create(
                                cod="z",
                                esta="Activo",
                                perfil=perfil,
                                repre_legal=repre_legal,
                                usu_crea = perfil_crea.user
                            )

                            # # Enviar el correo con la contraseña
                            # asunto = "Bienvenido a la plataforma"
                            # mensaje = f"Hola {fila['nom']} {fila['apelli']},\n\nTu cuenta ha sido creada con éxito. A continuación se encuentran tus credenciales:\n\nUsuario: {username}\nContraseña: {contraseña}\n\nRecuerda cambiar tu contraseña después de iniciar sesión."
                            # send_mail(
                            #     asunto,
                            #     mensaje,
                            #     settings.DEFAULT_FROM_EMAIL,
                            #     [fila['email']],
                            #     fail_silently=False,
                            # )

                            resumen["insertados"] += 1
                            messages.success(request, "Filas insertadas correctamente.")

                        except Exception as e:
                            errores.append(f"Error: {str(e)} en la fila {fila}")
                            resumen["errores"] += 1
                            resumen["insertados"] = 0
                            raise  # Fuerza el rollback

            except Exception as e:
                messages.error(request, "No se ha cargado informacion, corrija los errores e intentelo de nuevo.")

            # Resumen de los datos procesados
            return render(request, 'aprendiz_masivo_crear.html', {
                'form': form,
                'errores': errores,
                'resumen': resumen
            })

    else:
        form = CargarAprendicesMasivoForm()

    return render(request, 'aprendiz_masivo_crear.html', {'form': form})

@login_required
def listar_instituciones(request):
    municipio = request.GET.get('municipio')
    departamento = request.GET.get('departamento')
    zona = request.GET.get('zona')
    estado = request.GET.get('estado')
    ordenar_por = request.GET.get('ordenar_por')

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '').strip()

    order_column_index = request.GET.get('order[0][column]', 0)
    order_dir = request.GET.get('order[0][dir]', 'asc')

    columns = [
        'nom',
        'dire',
        'muni__nom_munici',
        'muni__nom_departa__nom_departa',
        'secto',
        'esta',
        'dane',
        'gene',
        'zona'
    ]

    try:
        order_column = columns[int(order_column_index)]
    except (IndexError, ValueError):
        order_column = 'nom'

    if order_dir == 'desc':
        order_column = f'-{order_column}'

    # Query inicial sin slicing
    queryset = T_insti_edu.objects.select_related('muni__nom_departa').order_by(order_column)
    total_records = queryset.count()

    # Filtros especiales (👈 mover arriba)
    if municipio:
        queryset = queryset.filter(muni__id=municipio)
    if departamento:
        queryset = queryset.filter(muni__nom_departa__id=departamento)
    if zona:
        queryset = queryset.filter(zona=zona)
    if estado:
        queryset = queryset.filter(esta=estado)

    # Ordenar por fecha personalizada
    if ordenar_por == 'fecha_asc':
        queryset = queryset.order_by('fecha_creacion')
    elif ordenar_por == 'fecha_desc':
        queryset = queryset.order_by('-fecha_creacion')

    # Búsqueda
    if search_value:
        queryset = queryset.filter(
            Q(nom__icontains=search_value) |
            Q(dire__icontains=search_value) |
            Q(muni__nom_munici__icontains=search_value) |
            Q(muni__nom_departa__nom_departa__icontains=search_value) |
            Q(secto__icontains=search_value) |
            Q(esta__icontains=search_value) |
            Q(dane__icontains=search_value) |
            Q(gene__icontains=search_value) |
            Q(zona__icontains=search_value)
        )

    total_filtered = queryset.count()

    queryset = queryset[start:start + length]

    data = [{
        'nom': i.nom,
        'dire': i.dire,
        'municipio_nombre': i.muni.nom_munici,
        'departamento_nombre': i.muni.nom_departa.nom_departa,
        'secto': i.secto,
        'esta': i.esta,
        'dane': i.dane,
        'gene': i.gene,
        'zona': i.zona,
        'id': i.id,
    } for i in queryset]

    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': total_filtered,
        'data': data,
    })

@login_required
def obtener_departamentos_filtro_insti(request):
    departamentos = (
        T_insti_edu.objects
        .select_related('muni__nom_departa') 
        .values('muni__nom_departa_id', 'muni__nom_departa__nom_departa') 
        .distinct()
        .order_by(Lower('muni__nom_departa__nom_departa'))
    )

    data = [
        {'value': depto['muni__nom_departa_id'], 'label': depto['muni__nom_departa__nom_departa']}
        for depto in departamentos if depto['muni__nom_departa__nom_departa']
    ]
    return JsonResponse(data, safe=False)

@login_required
def obtener_municipio_filtro_insti(request):
    departamento_id = request.GET.get('departamento_id')

    municipios_qs = T_insti_edu.objects.select_related('muni', 'muni__nom_departa')

    if departamento_id:
        municipios_qs = municipios_qs.filter(muni__nom_departa__id=departamento_id)

    municipios = (municipios_qs
                .values('muni_id', 'muni__nom_munici')
                .distinct()
                .order_by(Lower('muni__nom_munici')))

    data = [
        {'value': mun['muni_id'], 'label': mun['muni__nom_munici']}
        for mun in municipios if mun['muni__nom_munici']
    ]

    return JsonResponse(data, safe=False)

@login_required
def obtener_estado_filtro_insti(request):
    estados = (T_insti_edu.objects
                .values_list('esta', flat=True)
                .distinct()
                .order_by(Lower('esta')))

    data = [{'value': est, 'label': est.capitalize()} for est in estados if est]
    return JsonResponse(data, safe=False)

@login_required
def obtener_zona_filtro_insti(request):
    zonas = (T_insti_edu.objects
            .values_list('zona', flat=True)
            .distinct())

    zona_map = {'u': 'Urbana', 'r': 'Rural'}
    data = [{'value': zona, 'label': zona_map.get(zona, 'Desconocida')} for zona in zonas if zona]
    return JsonResponse(data, safe=False)

@login_required
def gestores(request):
    perfil_form = PerfilForm()
    gestores = T_gestor.objects.prefetch_related(
        Prefetch(
            't_gestor_depa_set', 
            queryset=T_gestor_depa.objects.select_related('depa')
        )
    )

    for gestor in gestores:
        gestor.departamentos = ', '.join(
            [depa.depa.nom_departa for depa in gestor.t_gestor_depa_set.all()]
        )

    return render(request, 'gestores.html', {
        'gestores': gestores,
        'perfil_form': perfil_form
    })

@login_required
def crear_gestor(request):
    if request.method == 'POST':
        perfil_form = PerfilForm(request.POST)
        departamentos = request.POST.getlist('departamentos[]')
        print(departamentos)
        if perfil_form.is_valid():
            dni = perfil_form.cleaned_data.get('dni')
            email = perfil_form.cleaned_data.get('mail')
            if T_perfil.objects.filter(dni__iexact = dni).exists():
                return JsonResponse({'status': 'error', 'message': 'Ya existe un usuario con ese DNI'}, status = 400)
            
            if T_perfil.objects.filter(mail__iexact = email).exists():
                return JsonResponse({'status': 'error', 'message': 'Ya existe un usuario con ese email'}, status = 400)
        
            if len(departamentos) == 0:
                return JsonResponse({'status': 'error', 'message': 'Debe seleccionar un departamento'}, status = 400)

            nombre = perfil_form.cleaned_data['nom']
            apellido = perfil_form.cleaned_data['apelli']
            base_username = (nombre[:3] + apellido[:3]).lower()
            username = base_username
            i = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{i}"
                i += 1

            # contraseña = generar_contraseña()

            # Crear el usuario con los datos generados
            new_user = User.objects.create_user(username=username, password=str(dni), email=perfil_form.cleaned_data['mail'])

            # Asignar usuario al perfil y guardarlo
            new_perfil = perfil_form.save(commit=False)
            new_perfil.user = new_user
            new_perfil.rol = 'gestor'
            new_perfil.mail = new_user.email
            new_perfil.save()

            # Crear el gestor
            new_gestor = T_gestor.objects.create(
                perfil = new_perfil,
                esta = "Activo"
            )

            for departamento in departamentos:
                departamento_obj = T_departa.objects.get(id=departamento)
                new_gestor_depa = T_gestor_depa(
                    gestor=new_gestor,
                    depa=departamento_obj,
                    fecha_crea=timezone.now(),
                    usuario_crea=request.user
                )
                new_gestor_depa.save()

            # # Enviar correo de bienvenida
            # asunto = "Credenciales de acceso"
            # mensaje = (
            #     f"Hola {new_perfil.nom},\n\n"
            #     f"Su cuenta ha sido creada exitosamente.\n"
            #     f"Usuario: {username}\n"
            #     f"Contraseña: {password}\n\n"
            #     f"Por favor cambie su contraseña después de iniciar sesión."
            # )
            # send_mail(
            #     asunto,
            #     mensaje,
            #     settings.DEFAULT_FROM_EMAIL,
            #     [new_perfil.mail],
            #     fail_silently=False,
            # )

            return JsonResponse({'status': 'success', 'message': 'Gestor creado con exito.'})
        else:
            errores_dict = perfil_form.errors.get_json_data()
            errores_custom = []

            for field, errors_list in errores_dict.items():
                nombre_campo = perfil_form.fields[field].label or field.capitalize()
                
                for err in errors_list:
                    mensaje = f"{nombre_campo}: {err['message']}"
                    errores_custom.append(mensaje)

            return JsonResponse({'status': 'error', 'message':'Errores en el formulario', 'errors': '<br>'.join(errores_custom)}, status = 400)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

@login_required 
def obtener_gestor(request, gestor_id):
    gestor = T_gestor.objects.filter(id=gestor_id).first()

    if gestor:
        departamentos = list(T_gestor_depa.objects.filter(gestor=gestor).values_list('depa__id', 'depa__nom_departa'))

        data = {
            'gestor-nom': gestor.perfil.nom,
            'gestor-apelli': gestor.perfil.apelli,
            'gestor-tipo_dni': gestor.perfil.tipo_dni,
            'gestor-dni': gestor.perfil.dni,
            'gestor-tele': gestor.perfil.tele,
            'gestor-dire': gestor.perfil.dire,
            'gestor-mail': gestor.perfil.mail,
            'gestor-gene': gestor.perfil.gene,
            'gestor-fecha_naci': gestor.perfil.fecha_naci,
            'departamentos': [{'id': dep[0], 'nom_departa': dep[1]} for dep in departamentos]
        }
        return JsonResponse(data)

    return JsonResponse({'status': 'error', 'message': 'Gestor no encontrado'}, status=404)

@login_required
def editar_gestor(request, gestor_id):
    gestor = get_object_or_404(T_gestor, pk=gestor_id)
    perfil = get_object_or_404(T_perfil, pk = gestor.perfil.id)

    if request.method == 'POST':
        form_perfil = PerfilForm(request.POST, instance=perfil)

        if form_perfil.is_valid():
            nuevos_departamentos = set(request.POST.getlist('departamentos'))
            if len(nuevos_departamentos) == 0:
                return JsonResponse({'status': 'error', 'message': 'El gestor debe tener almenos un departamento asociado.'}, status = 400)
            actuales_departamentos = set(
                T_gestor_depa.objects.filter(gestor=gestor).values_list('depa__id', flat=True)
            )

            # Identificar departamentos que se intentan eliminar
            departamentos_a_eliminar = actuales_departamentos - nuevos_departamentos

            # verificar si alguno de los deparatmentos a eliminar tiene instituciones asignadas
            departamentos_con_instituciones = T_gestor_insti_edu.objects.filter(
                gestor = gestor,
                insti__muni__nom_departa__id__in= departamentos_a_eliminar
            ).exists()

            if departamentos_con_instituciones:
                return JsonResponse({'status': 'error', 'message': 'No se puede actualizar. Uno o más departamentos tienen instituciones asignadas.'}, status=400)

            T_gestor_depa.objects.filter(gestor=gestor).delete()  # Elimina los existentes
            for depa in nuevos_departamentos:
                departamento = T_departa.objects.get(id=depa)
                T_gestor_depa.objects.create(
                    gestor=gestor, 
                    depa=departamento, 
                    fecha_crea = timezone.now(),
                    usuario_crea = request.user
                )

            form_perfil.save()

            return JsonResponse({'status': 'success', 'message': 'Gestor actualizado correctamente '}, status = 200)
        else:
            errors = {
                'perfil': form_perfil.errors,
            }
            return JsonResponse({'status': 'error', 'message': 'Error al actualizar el lider', 'errors': errors}, status = 400)
    return JsonResponse({'status': 'error', 'message': 'Metodo no permitido', 'errors': errors}, status = 405)

def reset_password_view(request):
    return render(request, 'res_con.html')

## GESTION DE USUARIOS ###
@login_required
def usuarios(request):
    usuarios = T_perfil.objects.all()
    return render(request, 'usuarios.html', {
        'usuarios': usuarios,
    })

@login_required
def restablecer_contrasena(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            nueva_contrasena = data.get('new_password')

            if not user_id or not nueva_contrasena:
                return JsonResponse({'status': 'error', 'message': 'Faltan datos'}, status=400)

            perfil = T_perfil.objects.filter(id=user_id).first()
            usuario = perfil.user
            if not perfil:
                return JsonResponse({'status': 'error', 'message': 'Usuario no encontrado'}, status=404)

            if not validar_contrasena_segura(nueva_contrasena):
                return JsonResponse({
                    'status': 'error',
                    'message': 'La contraseña debe tener al menos 8 caracteres, incluyendo mayúsculas, minúsculas, números y caracteres especiales.'
                }, status=400)

            usuario.password = make_password(nueva_contrasena)
            usuario.save()
            return JsonResponse({'status': 'success', 'message': 'Contraseña actualizada correctamente'}, status = 200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Metodo no permitido'}, status = 405)

def validar_contrasena_segura(password):
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=/\\[\]`~%$]', password):
        return False
    return True