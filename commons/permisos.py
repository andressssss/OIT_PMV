from functools import wraps
from django.http import JsonResponse

# FBV
from functools import wraps
from django.http import JsonResponse
from django.shortcuts import render

def bloquear_si_consulta(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        perfil = getattr(request.user, 't_perfil', None)
        if perfil and perfil.rol == 'consulta':
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({
                    'status': 'error',
                    'message': 'Su perfil no tiene permisos para realizar esta acción.'
                }, status=403)
            else:
                return render(request, '403.html', status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped_view



# DRF
from rest_framework.permissions import BasePermission

class DenegarConsulta(BasePermission):
    message = 'Su perfil no tiene permisos para realizar esta acción.'

    def has_permission(self, request, view):
        perfil = getattr(request.user, 't_perfil', None)
        if perfil and perfil.rol == 'consulta':
            return False
        return True
