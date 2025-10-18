from django.shortcuts import render
from commons.mixins import PermisosMixin
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required
def dashboard(request):
  mixin = PermisosMixin()
  mixin.modulo = "dashboard"

  acciones = mixin.get_permission_actions(request)
  puede_ver = acciones.get("ver", False)
  return render(request, 'dashboard.html', { "puede_ver": puede_ver })


def inbox_novedades(request):
  return render(request, 'inbox_novedades.html')