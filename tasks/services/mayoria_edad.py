from datetime import date, timedelta
from typing import Optional

from django.utils import timezone

from commons.models import T_apre


def _siguiente_cumpleanios_18(fecha_naci: date) -> Optional[date]:
    """Fecha en que el aprendiz cumple/cumplió 18 años. None si la fecha de
    nacimiento es inválida (p.ej. año fuera de rango por dato sucio)."""
    try:
        return fecha_naci.replace(year=fecha_naci.year + 18)
    except ValueError:
        try:
            # 29 de febrero -> 28 de febrero del año +18
            return fecha_naci.replace(year=fecha_naci.year + 18, day=28)
        except ValueError:
            return None


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


def tiene_cc_actualizado(aprendiz: T_apre) -> bool:
    """Verifica si el instructor marcó como resuelta la alerta de CC del
    aprendiz. Como en este proyecto las cédulas se consolidan en un PDF de
    la ficha (no hay carpeta individual por aprendiz), no es posible validar
    automáticamente el archivo. En su lugar, el instructor debe marcar la
    alerta como resuelta desde el panel de la ficha."""
    from tasks.models import T_notifi
    return T_notifi.objects.filter(
        origen_tipo='mayoria_edad',
        origen_id=aprendiz.id,
        nivel='riesgo',
        resuelta=True,
    ).exists()


def aprendices_para_alerta(dias_objetivo: int):
    """Aprendices cuyo conteo de días para 18 == dias_objetivo (puede ser
    negativo). Filtra a los que tienen fecha_naci. Devuelve lista."""
    hoy = timezone.localdate()
    fecha_objetivo = hoy + timedelta(days=dias_objetivo)
    # Cumpleaños 18 = fecha_objetivo => fecha_naci = fecha_objetivo - 18 años
    try:
        fecha_naci_objetivo = fecha_objetivo.replace(year=fecha_objetivo.year - 18)
    except ValueError:
        try:
            fecha_naci_objetivo = fecha_objetivo.replace(
                year=fecha_objetivo.year - 18, day=28,
            )
        except ValueError:
            return []
    return list(
        T_apre.objects
        .select_related('perfil', 'ficha__instru__perfil__user')
        .filter(perfil__fecha_naci=fecha_naci_objetivo, esta='activo')
    )
