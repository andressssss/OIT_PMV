from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from commons.models import T_instru, T_apre, T_admin, T_lider, T_nove, T_repre_legal
from .forms import InstructorForm, UserFormCreate, UserFormEdit, PerfilForm, NovedadForm, AdministradoresForm, AprendizForm, LiderForm, RepresanteLegalForm
from django.db import IntegrityError
from django.http import JsonResponse
from django.forms.models import model_to_dict

# Create your views here.


def home(request):
    return render(request, 'home.html')


def signin(request):
    if request.method == 'GET':
        return render(request, 'signin.html', {
            'form': AuthenticationForm
        })
    else:
        user = authenticate(
            request, username=request.POST['username'], password=request.POST['password'])
        if user is None:
            return render(request, 'signin.html', {
                'form': AuthenticationForm,
                'error': "El usuario o la contraseña es incorrecto"
            })
        else:
            login(request, user)
            return redirect('novedades')


def signup(request):
    if request.method == 'GET':
        return render(request, 'signup.html', {
            'form': UserCreationForm
        })
    else:
        if request.POST['password1'] == request.POST['password2']:
            try:
                user = User.objects.create_user(
                    username=request.POST['username'], password=request.POST['password1'])
                user.save()
                login(request, user)
                return redirect('tasks')
            except IntegrityError:
                return render(request, 'signup.html', {
                    'form': UserCreationForm,
                    'error': "El usuario ya existe"
                })
    return render(request, 'signup.html', {
        'form': UserCreationForm,
        'error': "Las contraseñas no coinciden"
    })


@login_required
def signout(request):
    logout(request)
    return redirect('home')


@login_required
def dashboard_admin(request):
    return render(request, 'admin_dashboard.html')

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
    aprendices = T_apre.objects.select_related('perfil__user').all()
    return render(request, 'aprendiz.html', {
        'aprendices': aprendices
    })


login_required


def crear_aprendices(request):  # Funcion para crear aprendiz
    if request.method == 'GET':

        user_form = UserFormCreate()
        perfil_form = PerfilForm()
        aprendiz_form = AprendizForm()

        return render(request, 'aprendiz_crear.html', {
            'user_form': user_form,
            'perfil_form': perfil_form,
            'aprendiz_form': aprendiz_form
        })
    else:
        try:
            user_form = UserFormCreate(request.POST)
            perfil_form = PerfilForm(request.POST)
            aprendiz_form = AprendizForm(request.POST)
            if user_form.is_valid() and perfil_form.is_valid() and aprendiz_form.is_valid():
                # Creacion del usuario
                new_user = user_form.save(commit=False)
                new_user.set_password(user_form.cleaned_data['password'])
                new_user.save()

                # creacion del perfil
                new_perfil = perfil_form.save(commit=False)
                new_perfil.user = new_user
                new_perfil.rol = 'aprendiz'
                new_perfil.mail = new_user.email
                new_perfil.save()

                # creacion del aprendiz
                new_aprendiz = aprendiz_form.save(commit=False)
                new_aprendiz.perfil = new_perfil
                new_aprendiz.save()
                return redirect('aprendices')

        except ValueError as e:
            return render(request, 'aprendiz_crear.html', {
                'user_form': user_form,
                'perfil_form': perfil_form,
                'aprendiz_form': aprendiz_form,
                'error': f'Ocurrió un error: {str(e)}'
            })


login_required


def detalle_aprendices(request, aprendiz_id):  # Funcion para editar aprendiz
    aprendiz = get_object_or_404(T_apre, pk=aprendiz_id)
    perfil = aprendiz.perfil
    user = perfil.user

    if request.method == 'GET':

        user_form = UserFormCreate(instance=user)
        perfil_form = PerfilForm(instance=perfil)
        aprendiz_form = AprendizForm(instance=aprendiz)

        return render(request, 'aprendiz_detalle.html', {
            'aprendiz': aprendiz,
            'user_form': user_form,
            'perfil_form': perfil_form,
            'aprendiz_form': aprendiz_form
        })
    else:
        try:
            user_form = UserFormCreate(request.POST)
            perfil_form = PerfilForm(request.POST)
            aprendiz_form = AprendizForm(request.POST)
            if user_form.is_valid() and perfil_form.is_valid() and aprendiz_form.is_valid():
                user_form.save()
                perfil_form.save()
                aprendiz_form.save()
            return redirect('aprendices')

        except ValueError:
            return render(request, 'aprendiz_detalle.html', {
                'user_form': user_form,
                'perfil_form': perfil_form,
                'aprendiz_form': aprendiz_form,
                'error': 'Error al actualizar el administrador. Verifique los datos'
            })


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
                new_perfil.rol = 'Lider'
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

        administrador_data['perfil'] = perfil_data

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
