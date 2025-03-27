from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from commons.models import T_oferta, T_cuentas, T_instru, T_oferta_instru, T_docu_labo, T_perfil
from .forms import OfertaCreateForm
from django.db.models import Q
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.http import JsonResponse


############################################################
##########  ¡OFERTAS!  #####################################
############################################################

# Listar ofertas############################################
@login_required
def ofertas(request):
    ofertas = T_oferta.objects.all()
    return render(request, 'ofertas.html', {
        'ofertas': ofertas,
    })

# Listar ofertas showcase ######################
@login_required
def ofertas_show(request):
    ofertas = T_oferta.objects.all()
    return render(request, 'ofertas_show.html', {
        'ofertas': ofertas,
    })

# Filtrar ofertas ########################################
def listar_ofertas(request):
    query = request.GET.get('search', '')  # Obtiene el término de búsqueda del input
    ofertas = T_oferta.objects.filter(
        Q(cargo__icontains=query) |
        Q(descri__icontains=query) |
        Q(profe_reque__icontains=query) |
        Q(depa__nom_departa__icontains=query) |
        Q(progra__nom__icontains=query)
    )
    return render(request, 'ofertas_show.html', {'ofertas': ofertas, 'search': query})

# Ver detalle de oferta ################################
def detalle_oferta(request, oferta_id):
    oferta = get_object_or_404(T_oferta, id=oferta_id)
    perfil = T_perfil.objects.filter(user = request.user).first()
    instructor = T_instru.objects.filter(perfil = perfil).first()
    usuario_postulado = T_oferta_instru.objects.filter(instru = instructor, ofe = oferta).exists()
    return render(request, 'ofertas_detalle.html', {
        'oferta': oferta,
        'usuario_postulado': usuario_postulado
        })

# Crear ofertas#############################################
@login_required
def crear_ofertas(request):
    if request.method == 'GET':
        oferta_form = OfertaCreateForm()
        return render(request, 'ofertas_crear.html', {
            'oferta_form': oferta_form
        })
    else:
        try:
            oferta_form = OfertaCreateForm(request.POST)
            if oferta_form.is_valid():
                # Creación del perfil
                new_oferta = oferta_form.save(commit=False)
                new_oferta.esta = 'creado'
                new_oferta.usu_cre = request.user
                new_oferta.save()
                return redirect('ofertas')
            else:
                return render(request, 'ofertas_crear.html', {
                    'oferta_form': oferta_form,
                    'error': 'Por favor corrige los errores en el formulario.'
                })
        except ValueError as e:
            return render(request, 'ofertas_crear.html', {
                'oferta_form': oferta_form,
                'error': f'Error: {str(e)}'
            })
        
# Postular oferta #################################

@login_required
def postular_oferta(request, oferta_id):
    # Obtener la oferta a la que el usuario desea postularse
    oferta = get_object_or_404(T_oferta, id=oferta_id)
    perfil = getattr(request.user, 't_perfil', None)
    # Verificar si el usuario ya se ha postulado
    usuario_instru = T_instru.objects.get(perfil = perfil.id)  # Asumiendo que hay una relación entre el usuario y T_instru
    postulado = T_oferta_instru.objects.filter(ofe=oferta, instru=usuario_instru).exists()
    
    if postulado:
        messages.error(request, "Ya te has postulado a esta oferta.")
        return redirect('ofertas_detalle', oferta_id=oferta_id)

    # Crear la postulación
    T_oferta_instru.objects.create(
        ofe=oferta,
        instru=usuario_instru,
        esta='postulado'  # Estado inicial de la postulación
    )
    usuario_instru.esta = 'Postulado'
    usuario_instru.save()
    
    messages.success(request, "Te has postulado a la oferta exitosamente.")
    return redirect('ofertas_detalle', oferta_id=oferta_id)

# Mis postulaciones ###########################
@login_required
def mis_postulaciones(request):
    perfil = getattr(request.user, 't_perfil', None)
    instructor = T_instru.objects.get(perfil=perfil.id)
    postulaciones = T_oferta_instru.objects.filter(instru=instructor.id) 

    return render(request, 'mis_postulaciones.html', {'postulaciones': postulaciones})

# Ver detalle postulacion #####################################
def ver_postulantes(request, oferta_id):
    # Obtener la oferta específica
    oferta = get_object_or_404(T_oferta, id=oferta_id)
    
    # Obtener las postulaciones de esa oferta
    postulaciones = T_oferta_instru.objects.filter(ofe=oferta)
    
    return render(request, 'ver_postulantes.html', {
        'oferta': oferta,
        'postulaciones': postulaciones
    })

# Ver detalle de postulacion>postulante ###################################
def ver_postulantes_detalle(request, postulacion_id):
    postulacion = T_oferta_instru.objects.get(id=postulacion_id)
    documentos = T_docu_labo.objects.filter(usu=postulacion.instru.perfil.user)
    return render(request, 'ver_postulantes_detalle.html', {
        'postulacion': postulacion,
        'documentos': documentos
    })

def rechazar_perfil(request, postulacion_id):
    if request.method == 'POST':
        motivo = request.POST.get("motivo_rechazo", "").strip()

        if not motivo:
            return JsonResponse({"success": False, "message": "Debe ingresar un motivo de rechazo."}, status=400)
        
        try:
            postulacion = T_oferta_instru.objects.filter(id = postulacion_id).first()
            postulacion.esta = "finalizado"
            postulacion.respuesta_rh = motivo
            postulacion.save()

            return JsonResponse({"success": True, "message": "Perfil rechazado correctamente"})
        except postulacion.DoesNotExist:
            return JsonResponse({"success": "False", "message": "La postulacion no existe"}, status=404)
    return JsonResponse({"success": False, "message": "Metodo no permitido"}, status=405)


def desistir_postulacion(request, postulacion_id):
    if request.method == 'POST':
        try:
            postulacion = T_oferta_instru.objects.filter(id = postulacion_id).first()
            postulacion.esta = "desistido"
            postulacion.save()

            return JsonResponse({"success": True, "message": "Desistido correctamente"})
        except postulacion.DoesNotExist:
            return JsonResponse({"success": "False", "message": "La postulacion no existe"}, status=404)
    return JsonResponse({"success": False, "message": "Metodo no permitido"}, status=405)
        
def contratos(request):
    return render(request, 'contratos.html')