from datetime import date, timedelta
from typing import Optional

from django.db.models import Q
from django.utils import timezone

from commons.models import T_apre, T_DocumentFolderAprendiz


def _siguiente_cumpleanios_18(fecha_naci: date) -> date:
    """Fecha en que el aprendiz cumple/cumplió 18 años."""
    try:
        return fecha_naci.replace(year=fecha_naci.year + 18)
    except ValueError:
        # 29 de febrero -> 28 de febrero del año +18
        return fecha_naci.replace(year=fecha_naci.year + 18, day=28)


def fecha_18(aprendiz: T_apre) -> Optional[date]:
    perfil = getattr(aprendiz, 'perfil', None)
    if not perfil or not perfil.fecha_naci:
        return None
    return _siguiente_cumpleanios_18(perfil.fecha_naci)


def dias_para_18(aprendiz: T_apre) -> Optional[int]:
    """Días hasta cumplir 18. Negativo si ya cumplió. None si no hay fecha_naci."""
    f18 = fecha_18(aprendiz)
    if f18 is None:
        return None
    hoy = timezone.localdate()
    return (f18 - hoy).days


def es_mayor_edad(aprendiz: T_apre) -> bool:
    dias = dias_para_18(aprendiz)
    return dias is not None and dias <= 0


PALABRAS_CC = ('cc', 'cedula', 'cédula', 'ciudadan')


def tiene_cc_actualizado(aprendiz: T_apre) -> bool:
    """Heurística: tipo_dni del perfil es 'cc' y existe en su portafolio un
    nodo documento cuyo nombre contiene "cc"/"cedula"/"ciudadan" con archivo
    cargado. La actualización del tipo_dni la hace manualmente el equipo."""
    perfil = getattr(aprendiz, 'perfil', None)
    if not perfil or perfil.tipo_dni != 'cc':
        return False

    cond = Q()
    for p in PALABRAS_CC:
        cond |= Q(name__icontains=p)

    return T_DocumentFolderAprendiz.objects.filter(
        aprendiz=aprendiz, tipo='documento', documento__isnull=False,
    ).filter(cond).exists()


def aprendices_para_alerta(dias_objetivo: int):
    """Aprendices cuyo conteo de días para 18 == dias_objetivo (puede ser
    negativo). Filtra a los que tienen fecha_naci. Devuelve queryset evaluado."""
    hoy = timezone.localdate()
    fecha_objetivo = hoy + timedelta(days=dias_objetivo)
    # Cumpleaños 18 = fecha_objetivo => fecha_naci = fecha_objetivo - 18 años
    try:
        fecha_naci_objetivo = fecha_objetivo.replace(year=fecha_objetivo.year - 18)
    except ValueError:
        fecha_naci_objetivo = fecha_objetivo.replace(
            year=fecha_objetivo.year - 18, day=28,
        )

    return list(
        T_apre.objects
        .select_related('perfil', 'ficha__instru__perfil__user')
        .filter(perfil__fecha_naci=fecha_naci_objetivo, esta='activo')
    )
