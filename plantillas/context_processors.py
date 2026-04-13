from commons.models import T_PlantillaAdmin


def plantilla_admin(request):
    if request.user.is_authenticated:
        return {
            "is_plantilla_admin": T_PlantillaAdmin.objects.filter(user=request.user).exists()
        }
    return {"is_plantilla_admin": False}
