from datetime import datetime
from typing import Optional

from django.db.models import Max
from django.utils import timezone

from commons.models import AuditLog, T_instru


ACCIONES_CONSIDERADAS = ['create', 'update', 'delete', 'login', 'download']


def ultima_actividad(instructor: T_instru) -> Optional[datetime]:
    """Devuelve la fecha más reciente entre last_login y la última entrada
    de AuditLog del usuario asociado al instructor. None si no hay datos."""
    user = getattr(instructor.perfil, 'user', None)
    if user is None:
        return None

    fechas = []
    if user.last_login:
        fechas.append(user.last_login)

    audit_max = (
        AuditLog.objects
        .filter(user=user, action__in=ACCIONES_CONSIDERADAS)
        .aggregate(m=Max('timestamp'))['m']
    )
    if audit_max:
        fechas.append(audit_max)

    return max(fechas) if fechas else None


def dias_sin_actividad(instructor: T_instru) -> Optional[int]:
    """Días enteros transcurridos desde la última actividad. None si nunca."""
    ultima = ultima_actividad(instructor)
    if ultima is None:
        return None
    delta = timezone.now() - ultima
    return delta.days


def instructores_inactivos(dias_minimos: int):
    """Generador de tuplas (instructor, dias_sin_actividad) para instructores
    cuyo conteo de días supera el umbral. Recorre sólo instructores activos."""
    qs = T_instru.objects.select_related('perfil__user').filter(
        perfil__user__is_active=True
    )
    for instructor in qs:
        dias = dias_sin_actividad(instructor)
        if dias is not None and dias >= dias_minimos:
            yield instructor, dias
