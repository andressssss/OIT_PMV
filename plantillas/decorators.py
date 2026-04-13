from functools import wraps
from django.http import JsonResponse
from django.shortcuts import redirect
from commons.models import T_PlantillaAdmin


def plantilla_admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('signin')
        if not T_PlantillaAdmin.objects.filter(user=request.user).exists():
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            if is_ajax or request.content_type == 'application/json':
                return JsonResponse({"error": "No autorizado"}, status=403)
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper
