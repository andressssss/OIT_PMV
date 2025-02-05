from django.utils.timezone import now
from django.contrib import messages
from django.shortcuts import redirect

class ExpiredSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            print(f"Usuario autenticado: {request.user}")
            sesion_expira = request.session.get_expiry_date()
            print(f"Expiración de la sesión: {sesion_expira}, Ahora: {now()}")
            if sesion_expira <= now():
                print("La sesión ha expirado")
                messages.error(request, "Tu sesión ha expirado. Por favor, inicia sesión nuevamente.")
                return redirect('login')
        return self.get_response(request)
