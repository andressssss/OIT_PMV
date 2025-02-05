from commons.models import T_perfil
from datetime import datetime
from django.utils.timezone import now
from django.contrib import messages

def perfil(request):
    if request.user.is_authenticated:
        try:
            perfil = T_perfil.objects.get(user=request.user)
            return {'perfil': perfil}
        except T_perfil.DoesNotExist:
            return {'perfil': None}
    return {'perfil': None}

def expiracion_sesion_context(request):
    if request.user.is_authenticated:
        sesion_expira = request.session.get_expiry_date()
        tiempo_restante = int((sesion_expira - now()).total_seconds())

        if tiempo_restante <= 0:
            messages.error(request, 'Tu sesión ha expirado. Por favor, inicia sesión nuevamente.')

        return {'tiempo_restante_sesion': tiempo_restante}

    return {'tiempo_restante_sesion': None}
