from django.forms import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.files.storage import default_storage
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from commons.models import T_instru,T_cuentas, T_gestor_insti_edu, T_apre,T_docu_labo, T_gestor_depa, T_gestor,T_docu, T_perfil, T_admin, T_lider, T_nove, T_repre_legal, T_munici, T_departa, T_insti_edu, T_centro_forma
from .forms import InstructorForm, PerfilEForm, CustomPasswordChangeForm, DocumentoLaboralForm, GestorForm, PerfilEditForm, GestorDepaForm, CargarAprendicesMasivoForm, UserFormCreate, UserFormEdit, PerfilForm, NovedadForm, AdministradoresForm, AprendizForm, LiderForm, RepresanteLegalForm, DepartamentoForm, MunicipioForm, InstitucionForm, CentroFormacionForm
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
from django.db.models.functions import Lower
import csv
import random
import string

def home(request):
    return render(request, 'home.html')

def signin(request):
    if request.user.is_authenticated:
        return redirect('home')  # Reemplaza 'dashboard' con la vista deseada

    if request.method == 'GET':
        return render(request, 'signin.html', {
            'form': AuthenticationForm
        })
    else:
        # Autenticación del usuario
        user = authenticate(
            request, username=request.POST['username'], password=request.POST['password'])
        
        if user is None:
            return render(request, 'signin.html', {
                'form': AuthenticationForm,
                'error': "El usuario o la contraseña es incorrecto"
            })
        else:
            login(request, user)
            
            # Obtener el perfil del usuario
            try:
                perfil = T_perfil.objects.get(user=user)  # Obtener el perfil asociado al usuario
                # Verificar el rol del perfil
                if perfil.rol == 'aprendiz':
                    print("1")
                    return redirect('panel_aprendiz')  # Redirigir al panel del aprendiz
                elif perfil.rol in ['gestor', 'lider']:
                    print("2")
                    return redirect('instituciones_gestor')
                elif perfil.rol == 'instructor':
                    print("3")
                    return redirect('ofertas_show')
            except T_perfil.DoesNotExist:
                pass  # Si no se encuentra el perfil, no hacer nada adicional

            # Si no es aprendiz, redirigir a novedades
            return redirect('novedades')

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
            form_perfil = PerfilForm(request.POST, instance=request.user.t_perfil)

            if form_perfil.is_valid():
                datos_actualizados = form_perfil.cleaned_data
                print(datos_actualizados)
                if 'fecha_naci' not in datos_actualizados or datos_actualizados['fecha_naci'] is None:
                    print("No viene fecha")
                    perfil_fe = T_perfil.objects.get(id = request.user.t_perfil.id)
                    form_perfil.instance.fecha_naci = perfil_fe.fecha_naci
                    print(form_perfil.instance.fecha_naci)
                form_perfil.save()
                messages.success(request, "Perfil actualizado correctamente.")
                return redirect('perfil')

                
            # Manejo del correo electrónico
            nuevo_email = request.POST.get('email')
            if nuevo_email:
                usuario_act = User.objects.get(id=request.user.id)
                usuario_act.email = nuevo_email
                usuario_act.save()
                perfil_act = T_perfil.objects.get(user=usuario_act)
                perfil_act.mail = nuevo_email
                perfil_act.save()

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
    return render(request, 'instructor.html', {
        'instructores': instructores
    })

@login_required
def crear_instructor(request):

    if request.method == 'GET':

        user_form = UserFormCreate()
        perfil_form = PerfilForm()
        instructor_form = InstructorForm()

        return render(request, 'instructor_crear.html', {
            'user_form': user_form,
            'perfil_form': perfil_form,
            'instructor_form': instructor_form
        })
    else:
        try:
            user_form = UserFormCreate(request.POST)
            perfil_form = PerfilForm(request.POST)
            instructor_form = InstructorForm(request.POST)
            if user_form.is_valid() and perfil_form.is_valid() and instructor_form.is_valid():
                # Creacion del usuario
                new_user = user_form.save(commit=False)
                new_user.set_password(user_form.cleaned_data['password'])
                new_user.save()

                # creacion del perfil
                new_perfil = perfil_form.save(commit=False)
                new_perfil.user = new_user
                new_perfil.rol = 'instructor'
                new_perfil.mail = new_user.email
                new_perfil.save()

                # creacion del instructor
                new_instructor = instructor_form.save(commit=False)
                new_instructor.perfil = new_perfil
                new_instructor.save()
                return redirect('instructores')

        except ValueError as e:
            return render(request, 'crear_instructor.html', {
                'user_form': user_form,
                'perfil_form': perfil_form,
                'instructor_form': instructor_form,
                'error': f'Ocurrió un error: {str(e)}'
            })

@login_required
def instructor_detalle(request, instructor_id):
    instructor = get_object_or_404(T_instru, pk=instructor_id)
    perfil = instructor.perfil
    user = perfil.user

    if request.method == 'GET':
        user_form = UserFormEdit(instance=user)
        perfil_form = PerfilForm(instance=perfil)
        instructor_form = InstructorForm(instance=instructor)
        return render(request, 'instructor_detalle.html', {
            'instructor': instructor,
            'user_form': user_form,
            'perfil_form': perfil_form,
            'instructor_form': instructor_form
        })
    else:
        try:
            # Si se envía el formulario con los datos modificados
            user_form = UserFormEdit(request.POST, instance=user)
            perfil_form = PerfilForm(request.POST, instance=perfil)
            instructor_form = InstructorForm(request.POST, instance=instructor)
            if user_form.is_valid() and perfil_form.is_valid() and instructor_form.is_valid():
                user_form.save()
                perfil_form.save()
                instructor_form.save()
                # Redirigir a la lista de instructores (ajusta según sea necesario)
                return redirect('instructores')
        except ValueError:
            # Si ocurre un error al guardar, mostrar el formulario nuevamente con el mensaje de error
            return render(request, 'instructor_detalle.html', {
                'instructor': instructor,
                'user_form': user_form,
                'perfil_form': perfil_form,
                'instructor_form': instructor_form,
                'error': "Error al actualizar el instructor. Verifique los datos."})

@login_required
def instructor_detalle_tabla(request, instructor_id):
    try:
        instructor = get_object_or_404(T_instru, pk=instructor_id)
        instructor_data = model_to_dict(instructor)

        # Incluimos datos relacionados del perfil
        if hasattr(instructor, 'perfil'):
            perfil_data = model_to_dict(instructor.perfil)

            # Si el perfil tiene una relación con Usuario, la agregamos
            if hasattr(instructor.perfil, 'user'):
                perfil_data['user'] = {
                    'username': instructor.perfil.user.username,
                    'email': instructor.perfil.user.email,
                    'first_name': instructor.perfil.user.first_name,
                    'last_name': instructor.perfil.user.last_name,
                }

        instructor_data['perfil'] = perfil_data

        return JsonResponse({'info_adicional': instructor_data})
    except T_instru.DoesNotExist:
        return JsonResponse({'error': 'Registro no encontrado'}, status=404)

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

### REP. LEGAL ###

@login_required
def representante_legal(request):
    representantes_legales = T_repre_legal.objects.all()
    return render(request, 'representantesLegales.html', {
        'representantesLegales': representantes_legales
    })

@login_required  # Funcion para crear Representante legal
def crear_representante_legal(request):
    if request.method == 'GET':

        replegal_form = RepresanteLegalForm()
        return render(request, 'representanteLegal_crear.html', {
            'replegal_form': replegal_form
        })
    else:
        try:
            replegal_form = RepresanteLegalForm(request.POST)
            if replegal_form.is_valid():
                new_represanteLegal = replegal_form.save(commit=False)
                new_represanteLegal.save()
                return redirect('represantesLegales')
        except ValueError as e:
            return render(request, 'representanteLegal_crear.html', {
                'replegal_form': replegal_form,
                'error': f'Ocurrió un error: {str(e)}'
            })

@login_required  # Funcion para Actualizar Representante legal
def detalle_representante_legal(request, repreLegal_id):
    representante_legal = get_object_or_404(T_repre_legal, id=repreLegal_id)

    if request.method == 'GET':

        replegal_form = RepresanteLegalForm(instance=representante_legal)
        return render(request, 'representanteLegal_detalle.html', {
            'represante_legal': representante_legal,
            'replegal_form': replegal_form
        })
    else:
        try:
            replegal_form = RepresanteLegalForm(
                request.POST, instance=representante_legal)
            if replegal_form.is_valid():
                replegal_form.save()
                return redirect('represantesLegales')
        except ValueError:
            return render(request, 'representanteLegal_detalle.html', {
                'replegal_form': replegal_form,
                'error': 'Error al actualizar el administrador. Verifique los datos'
            })

@login_required  # Funcion para eliminar  Representante legal
def eliminar_representante_legal(request, repreLegal_id):
    representante_legal = get_object_or_404(T_repre_legal, id=repreLegal_id)
    if request.method == 'POST':
        representante_legal.delete()
        return redirect('represantesLegales')
    return render(request, 'confirmar_eliminacion_represante_legal.html', {
        'represante_legal': representante_legal,
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
def obtener_usuarios_creacion(request):
    usuarios_ids = T_apre.objects.values_list('usu_crea', flat=True,).distinct()

    # Obtener los perfiles relacionados a esos usuarios
    perfiles = T_perfil.objects.filter(user__id__in=usuarios_ids).values('nom', 'apelli').distinct()

    # Formatear como "Nombre Apellido"
    usuarios = [f"{perfil['nom']} {perfil['apelli']}" for perfil in perfiles]

    return JsonResponse(usuarios, safe=False)

def obtener_opciones_estados(request):
    estados = T_apre.objects.values_list('esta', flat=True).distinct()
    return JsonResponse(list(estados), safe=False)

## Endpoint para filtrar aprendices en la tabla ##
def filtrar_aprendices(request):
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
                    edad = (datetime.now().date() - fecha_nacimiento).days // 365
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

                contraseña = generar_contraseña()

                new_user = User.objects.create_user(
                    username=username,
                    password=contraseña,
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
    return render(request, 'lideres.html', {
        'lideres': lideres
    })

@login_required  # Funcion para crear lider
def crear_lideres(request):

    if request.method == 'GET':
        user_form = UserFormCreate()
        perfil_form = PerfilForm()
        lider_form = LiderForm()
        return render(request, 'lider_crear.html', {
            'user_form': user_form,
            'perfil_form': perfil_form,
            'lider_form': lider_form
        })
    else:
        try:
            # Si se envía el formulario con los datos modificados
            user_form = UserFormCreate(request.POST)
            perfil_form = PerfilForm(request.POST)
            lider_form = LiderForm(request.POST)
            if user_form.is_valid() and perfil_form.is_valid() and lider_form.is_valid():
                new_user = user_form.save(commit=False)
                new_user.set_password(user_form.cleaned_data['password'])
                new_user.save()
                new_perfil = perfil_form.save(commit=False)
                new_perfil.user = new_user
                new_perfil.rol = 'lider'
                new_perfil.save()
                new_lider = lider_form.save(commit=False)
                new_lider.perfil = new_perfil
                new_lider.save()
                return redirect('lideres')
            else:
                # Manejo de formularios inválidos
                return render(request, 'lider_crear.html', {
                    'user_form': user_form,
                    'perfil_form': perfil_form,
                    'lider_form':  lider_form,
                    'error': "Datos inválidos en el formulario. Corrige los errores."
                })
        except ValueError:
            # Si ocurre un error al guardar, mostrar el formulario nuevamente con el mensaje de error
            return render(request, 'lider_crear.html', {
                'user_form': user_form,
                'perfil_form': perfil_form,
                'lider_form': lider_form,
                'error': "Se presenta un error al crear el lider"})


@login_required  # Funcion para actualizar informacion de lider
def detalle_lideres(request, lider_id):
    lider = get_object_or_404(T_lider, id=lider_id)
    perfil = lider.perfil
    user = perfil.user

    if request.method == 'GET':
        user_form = UserFormEdit(instance=user)
        perfil_form = PerfilForm(instance=perfil)
        lider_form = LiderForm(instance=lider)
        return render(request, 'lider_detalle.html', {
            'lider': lider,
            'user_form': user_form,
            'perfil_form': perfil_form,
            'lider_form': lider_form
        })
    else:
        try:
            # Si se envía el formulario con los datos modificados
            user_form = UserFormEdit(request.POST, instance=user)
            perfil_form = PerfilForm(request.POST, instance=perfil)
            lider_form = LiderForm(request.POST, instance=lider)
            if user_form.is_valid() and perfil_form.is_valid() and lider_form.is_valid():

                user_form.save()
                perfil_form.save()
                lider_form.save()
                return redirect('lideres')

        except ValueError:
            # Si ocurre un error al guardar, mostrar el formulario nuevamente con el mensaje de error
            return render(request, 'lider_detalle.html', {
                'user_form': user_form,
                'perfil_form': perfil_form,
                'lider_form': lider_form,
                'error': "Error al actualizar el lider. Verifique los datos."})


@login_required
def eliminar_lideres(request, lider_id):  # Funcion para eliminar informacion de lider
    lider = get_object_or_404(T_lider, id=lider_id)
    if request.method == 'POST':
        lider.delete()
        return redirect('lideres')
    return render(request, 'confirmar_eliminacion_lider.html', {
        'lider': lider
    })

### ADMINISTRADOR ###


@login_required
def administradores(request):
    administradores = T_admin.objects.select_related('perfil__user').all()
    return render(request, 'administradores.html', {
        'administradores': administradores
    })


@login_required
def crear_administradores(request):  # funcion para crear administradores

    if request.method == 'GET':
        user_form = UserFormCreate()
        perfil_form = PerfilForm()
        admin_form = AdministradoresForm()

        return render(request, 'administradores_crear.html', {
            'admin_form': admin_form,
            'perfil_form': perfil_form,
            'user_form':  user_form
        })
    else:
        try:
            # Si se envía el formulario con los datos modificados
            user_form = UserFormCreate(request.POST)
            perfil_form = PerfilForm(request.POST)
            admin_form = AdministradoresForm(request.POST)
            if user_form.is_valid() and perfil_form.is_valid() and admin_form.is_valid():
                new_user = user_form.save(commit=False)
                new_user.set_password(user_form.cleaned_data['password'])
                new_user.save()
                new_perfil = perfil_form.save(commit=False)
                new_perfil.user = new_user
                new_perfil.rol = 'admin'
                new_perfil.save()
                new_admin = admin_form.save(commit=False)
                new_admin.perfil = new_perfil
                new_admin.save()
                return redirect('administradores')
            else:
                # Manejo de formularios inválidos
                return render(request, 'administradores_crear.html', {
                    'user_form': user_form,
                    'perfil_form': perfil_form,
                    'admin_form': admin_form,
                    'error': "Datos inválidos en el formulario. Corrige los errores."
                })
        except ValueError:
            # Si ocurre un error al guardar, mostrar el formulario nuevamente con el mensaje de error
            return render(request, 'administradores_crear.html', {
                'user_form': user_form,
                'perfil_form': perfil_form,
                'admin_form': admin_form,
                'error': "Error al actualizar el administrador. Verifique los datos."})


@login_required
# funcion para actualizar informacion de los administradores
def detalle_administradores(request, admin_id):
    administrador = get_object_or_404(T_admin, id=admin_id)
    perfil = administrador.perfil
    user = perfil.user

    if request.method == 'GET':
        user_form = UserFormEdit(instance=user)
        perfil_form = PerfilForm(instance=perfil)
        admin_form = AdministradoresForm(instance=administrador)

        return render(request, 'administradores_detalle.html', {
            'administrador': administrador,
            'admin_form': admin_form,
            'perfil_form': perfil_form,
            'user_form':  user_form
        })
    else:
        try:
            # Si se envía el formulario con los datos modificados
            user_form = UserFormEdit(request.POST, instance=user)
            perfil_form = PerfilForm(request.POST, instance=perfil)
            admin_form = AdministradoresForm(
                request.POST, instance=administrador)
            if user_form.is_valid() and perfil_form.is_valid() and admin_form.is_valid():
                user_form.save()
                perfil_form.save()
                admin_form.save()

                # Redirigir a la lista de administradores (ajusta según sea necesario)
                return redirect('administradores')
        except ValueError:
            # Si ocurre un error al guardar, mostrar el formulario nuevamente con el mensaje de error
            return render(request, 'administradores_detalle.html', {
                'user_form': user_form,
                'perfil_form': perfil_form,
                'admin_form': admin_form,
                'error': "Error al actualizar el administrador. Verifique los datos."})


@login_required
def eliminar_admin(request, admin_id):  # Funcion para eliminar informacion del admin
    admin = get_object_or_404(T_admin, pk=admin_id)
    if request.method == 'POST':
        admin.delete()
        return redirect('administradores')
    return render(request, 'confirmar_eliminacion_administradores.html', {'admin': admin})


@login_required
def administrador_detalle_tabla(request, admin_id):
    try:
        administrador = get_object_or_404(T_admin, id=admin_id)
        administrador_data = model_to_dict(administrador)

        # Incluimos datos relacionados del perfil
        if hasattr(administrador, 'perfil'):
            administrador_data = model_to_dict(administrador.perfil)

            # Si el perfil tiene una relación con Usuario, la agregamos
            if hasattr(administrador.perfil, 'user'):
                administrador_data['user'] = {
                    'username': administrador.perfil.user.username,
                    'email': administrador.perfil.user.email,
                    'first_name': administrador.perfil.user.first_name,
                    'last_name': administrador.perfil.user.last_name,
                }

        administrador_data['perfil'] = administrador_data

        return JsonResponse({'info_adicional': administrador_data})
    except T_instru.DoesNotExist:
        return JsonResponse({'error': 'Registro no encontrado'}, status=404)

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


def eliminar_departamentos(request, departamento_id):
    departamento = get_object_or_404(T_departa, id=departamento_id)
    if request.method == 'POST':
        departamento.delete()
        return redirect('departamentos')
    return render(request, 'confirmar_eliminacion_departamento.html', {
        'departamento': departamento,
    })


## MUNICIPIOS ##
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
                new_institucion.vigen = datetime.now().year
                new_institucion.save()

                return JsonResponse({'status':'success', 'message': 'Institución creada correctamente.'}, status=200)

            errors = institucionForm.errors.as_ul()
            return JsonResponse({'status': 'error','message': 'Valide el formulario nuevamente', 'errors': errors}, status=400)

        except ValueError as e:
            errors = "<ul><li>Error interno: {}</li></ul>".format(str(e))
            return JsonResponse({'status':'error','errors': errors}, status=500)

    else:
        return JsonResponse({"errors": "<ul><li>Método no permitido.</li></ul>"}, status=405)

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

def obtener_municipios(request):
    departamento_id = request.GET.get('departamento_id')
    if departamento_id:
        municipios = T_munici.objects.filter(nom_departa_id=departamento_id).values('id', 'nom_munici')
        return JsonResponse(list(municipios), safe=False)
    return JsonResponse({'error': 'No se proporcionó el ID del departamento'}, status=400)

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
                                    # Intentar convertir la fecha en formato "1/01/1980"
                                    fecha_naci = datetime.strptime(fecha_naci_str, '%d/%m/%Y')
                                    # Convertirla al formato YYYY-MM-DD
                                    fecha_naci = fecha_naci.strftime('%Y-%m-%d')
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
                            contraseña = generar_contraseña()

                            # Crear el usuario
                            user = User.objects.create_user(
                                username=username,
                                password=contraseña,
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

def obtener_estado_filtro_insti(request):
    estados = (T_insti_edu.objects
                .values_list('esta', flat=True)
                .distinct()
                .order_by(Lower('esta')))

    data = [{'value': est, 'label': est.capitalize()} for est in estados if est]
    return JsonResponse(data, safe=False)

def obtener_zona_filtro_insti(request):
    zonas = (T_insti_edu.objects
            .values_list('zona', flat=True)
            .distinct())

    zona_map = {'u': 'Urbana', 'r': 'Rural'}
    data = [{'value': zona, 'label': zona_map.get(zona, 'Desconocida')} for zona in zonas if zona]
    return JsonResponse(data, safe=False)

@login_required
def gestores(request):
    # Obtén todos los gestores junto con sus departamentos asociados
    gestores = T_gestor.objects.prefetch_related(
        Prefetch(
            't_gestor_depa_set',  # Nombre del related_name entre gestor y gestor-depa
            queryset=T_gestor_depa.objects.select_related('depa')
        )
    )

    # Añade un atributo personalizado para concatenar los departamentos
    for gestor in gestores:
        gestor.departamentos = ', '.join(
            [depa.depa.nom_departa for depa in gestor.t_gestor_depa_set.all()]
        )

    return render(request, 'gestores.html', {
        'gestores': gestores
    })

@login_required
def crear_gestor(request):
    if request.method == 'GET':
        perfil_form = PerfilForm()
        gestor_depa_form = GestorDepaForm()

        return render(request, 'gestor_crear.html', {
            'perfil_form': perfil_form,
            'gestor_depa_form': gestor_depa_form
        })
    else:
        try:
            perfil_form = PerfilForm(request.POST)
            gestor_depa_form = GestorDepaForm(request.POST)

            if perfil_form.is_valid() and gestor_depa_form.is_valid():
                # Obtener datos del perfil
                new_perfil = perfil_form.save(commit=False)

                # Verificar si ya existe un gestor con la misma cédula
                if T_perfil.objects.filter(dni=new_perfil.dni, rol="gestor").exists():
                    messages.error(
                    request,
                    "Ya existe un gestor con esta cédula"
                    )
                    return render(request, 'gestor_crear.html', {
                        'perfil_form': perfil_form,
                        'gestor_depa_form': gestor_depa_form,
                        'error': 'Ya existe un gestor con esta cédula.'
                    })

                # Generar username automáticamente
                username_base = new_perfil.nom.lower().replace(" ", "")  # Eliminar espacios
                username = f"{username_base}g"

                # Asegurar que el username sea único
                count = 1
                while User.objects.filter(username=username).exists():
                    username = f"{username_base}g{count}"
                    count += 1

                # Generar una contraseña aleatoria
                password = generar_contraseña()

                # Crear el usuario con los datos generados
                new_user = User.objects.create_user(username=username, password=password, email=new_perfil.mail)

                # Asignar usuario al perfil y guardarlo
                new_perfil.user = new_user
                new_perfil.rol = 'gestor'
                new_perfil.save()

                # Crear el gestor
                new_gestor = T_gestor(perfil=new_perfil, esta='asignado')
                new_gestor.save()

                # Crear relación con departamentos
                departamentos = gestor_depa_form.cleaned_data['departamentos']
                for departamento in departamentos:
                    departai = T_departa.objects.get(nom_departa=departamento)
                    new_gestor_depa = T_gestor_depa(
                        gestor=new_gestor,
                        depa=departai,
                        fecha_crea=datetime.now(),
                        usuario_crea=request.user
                    )
                    new_gestor_depa.save()

                # Enviar correo de bienvenida
                asunto = "Credenciales de acceso"
                mensaje = (
                    f"Hola {new_perfil.nom},\n\n"
                    f"Su cuenta ha sido creada exitosamente.\n"
                    f"Usuario: {username}\n"
                    f"Contraseña: {password}\n\n"
                    f"Por favor cambie su contraseña después de iniciar sesión."
                )
                send_mail(
                    asunto,
                    mensaje,
                    settings.DEFAULT_FROM_EMAIL,
                    [new_perfil.mail],
                    fail_silently=False,
                )

                return redirect('gestores')

            else:
                return render(request, 'gestor_crear.html', {
                    'perfil_form': perfil_form,
                    'gestor_depa_form': gestor_depa_form,
                    'error': 'Por favor corrige los errores en el formulario.'
                })

        except ValueError as e:
            return render(request, 'gestor_crear.html', {
                'perfil_form': perfil_form,
                'gestor_depa_form': gestor_depa_form,
                'error': f'Error: {str(e)}'
            })

@login_required
def gestor_detalle(request, gestor_id):
    gestor = get_object_or_404(T_gestor, pk=gestor_id)
    perfil = gestor.perfil
    user = perfil.user

    if request.method == 'GET':
        perfil_form = PerfilEditForm(instance=perfil)

        # Seleccionar los departamentos asociados al gestor
        departamentos_asignados = T_gestor_depa.objects.filter(gestor=gestor).values_list('depa', flat=True)
        gestor_depa_form = GestorDepaForm(
            initial={'departamentos': departamentos_asignados}
        )

        return render(request, 'gestor_detalle.html', {
            'gestor': gestor,
            'perfil_form': perfil_form,
            'gestor_depa_form': gestor_depa_form
        })
    elif request.method == 'POST':
        perfil_form = PerfilEditForm(request.POST, instance=perfil)
        gestor_depa_form = GestorDepaForm(request.POST)

        if perfil_form.is_valid() and gestor_depa_form.is_valid():

            # Actualizar departamentos asociados
            nuevos_departamentos = set(
                gestor_depa_form.cleaned_data['departamentos'].values_list('id', flat=True)
            )
            actuales_departamentos = set(
                T_gestor_depa.objects.filter(gestor=gestor).values_list('depa__id', flat=True)
            )

            # Identificar departamentos que se intentan eliminar
            departamentos_a_eliminar = actuales_departamentos - nuevos_departamentos
            print(nuevos_departamentos)
            print(actuales_departamentos)
            print(departamentos_a_eliminar)
            # verificar si alguno de los deparatmentos a eliminar tiene instituciones asignadas
            departamentos_con_instituciones = T_gestor_insti_edu.objects.filter(
                gestor = gestor,
                insti__muni__nom_departa__id__in= departamentos_a_eliminar
            ).exists()

            if departamentos_con_instituciones:
                messages.error(
                    request,
                    "No se puede actualizar. Uno o mas departamentos que intenta eliminar tiene instituciones asiganadas"
                )
                return render(request, 'gestor_detalle.html', {
                    'gestor': gestor,
                    'perfil_form': perfil_form,
                    'gestor_depa_form': gestor_depa_form,
                })

            # Si no hay problemas, guarda el perfin
            perfil_form.save()
            
            T_gestor_depa.objects.filter(gestor=gestor).delete()  # Elimina los existentes
            for depa in nuevos_departamentos:
                departamento = T_departa.objects.get(id=depa)
                T_gestor_depa.objects.create(
                    gestor=gestor, 
                    depa=departamento, 
                    fecha_crea = datetime.now(),
                    usuario_crea = request.user
                )

            return redirect('gestores')

        return render(request, 'gestor_detalle.html', {
            'gestor': gestor,
            'perfil_form': perfil_form,
            'gestor_depa_form': gestor_depa_form,
        })

# @login_required
# def instructor_detalle(request, instructor_id):
#     instructor = get_object_or_404(T_instru, pk=instructor_id)
#     perfil = instructor.perfil
#     user = perfil.user

#     if request.method == 'GET':
#         user_form = UserFormEdit(instance=user)
#         perfil_form = PerfilForm(instance=perfil)
#         instructor_form = InstructorForm(instance=instructor)
#         return render(request, 'instructor_detalle.html', {
#             'instructor': instructor,
#             'user_form': user_form,
#             'perfil_form': perfil_form,
#             'instructor_form': instructor_form
#         })
#     else:
#         try:
#             # Si se envía el formulario con los datos modificados
#             user_form = UserFormEdit(request.POST, instance=user)
#             perfil_form = PerfilForm(request.POST, instance=perfil)
#             instructor_form = InstructorForm(request.POST, instance=instructor)
#             if user_form.is_valid() and perfil_form.is_valid() and instructor_form.is_valid():
#                 user_form.save()
#                 perfil_form.save()
#                 instructor_form.save()
#                 # Redirigir a la lista de instructores (ajusta según sea necesario)
#                 return redirect('instructores')
#         except ValueError:
#             # Si ocurre un error al guardar, mostrar el formulario nuevamente con el mensaje de error
#             return render(request, 'instructor_detalle.html', {
#                 'instructor': instructor,
#                 'user_form': user_form,
#                 'perfil_form': perfil_form,
#                 'instructor_form': instructor_form,
#                 'error': "Error al actualizar el instructor. Verifique los datos."})
