import logging

from celery import shared_task

from commons.models import T_DocumentFolderAprendiz
from tasks.models import T_alerta_regla
from tasks.services.inactividad import instructores_inactivos
from tasks.services.mayoria_edad import (
    aprendices_para_alerta, dias_para_18, tiene_cc_actualizado,
)
from tasks.services.notificaciones import emitir_alerta


logger = logging.getLogger(__name__)


@shared_task(name="tasks.ping")
def ping():
    logger.info("Celery ping OK")
    return "pong"


@shared_task(name="tasks.evaluar_inactividad_instructores")
def evaluar_inactividad_instructores():
    """Recorre las reglas de inactividad activas y emite alertas para los
    instructores cuyo conteo de días sin actividad supera el umbral.

    La regla con mayor umbral gana: si un instructor califica para 'seguimiento',
    no se le emite también 'preventiva'.
    """
    reglas = list(
        T_alerta_regla.objects
        .filter(activa=True, tipo__startswith='inactividad_')
        .order_by('-dias_umbral')
    )
    if not reglas:
        logger.info('No hay reglas activas de inactividad.')
        return

    ya_alertados = set()
    total = 0

    for regla in reglas:
        for instructor, dias in instructores_inactivos(regla.dias_umbral):
            if instructor.id in ya_alertados:
                continue
            ya_alertados.add(instructor.id)

            perfil = instructor.perfil
            contexto = {
                'nombre': f'{perfil.nom} {perfil.apelli}'.strip(),
                'dni': perfil.dni,
                'dias': dias,
            }
            total += emitir_alerta(
                regla=regla,
                origen_id=instructor.id,
                contexto=contexto,
            )

    logger.info('evaluar_inactividad_instructores: %s notificaciones emitidas', total)
    return total


def _instructor_user(aprendiz):
    """Devuelve el `User` del instructor asignado a la ficha del aprendiz."""
    ficha = getattr(aprendiz, 'ficha', None)
    if not ficha or not ficha.instru_id:
        return None
    perfil = getattr(ficha.instru, 'perfil', None)
    return getattr(perfil, 'user', None) if perfil else None


def _asegurar_carpeta_cc(aprendiz):
    """Crea (si no existe) una carpeta sugerida para cargar el CC actualizado."""
    nombre = 'Cédula de ciudadanía (mayoría de edad)'
    raiz = T_DocumentFolderAprendiz.objects.filter(
        aprendiz=aprendiz, parent__isnull=True
    ).first()
    if not raiz:
        return None
    existe = T_DocumentFolderAprendiz.objects.filter(
        aprendiz=aprendiz, parent=raiz, name=nombre
    ).exists()
    if existe:
        return None
    return T_DocumentFolderAprendiz.objects.create(
        aprendiz=aprendiz, parent=raiz, name=nombre, tipo='carpeta',
    )


@shared_task(name="tasks.seguimiento_mayoria_edad")
def seguimiento_mayoria_edad():
    """Genera alertas relacionadas con la mayoría de edad de aprendices:
    - 30 días antes del cumpleaños 18 (preventiva al instructor)
    - El día del cumpleaños (al instructor)
    - +N días sin CC actualizado (riesgo, al admin)
    """
    total = 0

    # Preventiva (-N días)
    regla_prev = T_alerta_regla.objects.filter(
        tipo='mayoria_edad_preventiva', activa=True
    ).first()
    if regla_prev:
        for apre in aprendices_para_alerta(regla_prev.dias_umbral):
            extras = []
            if regla_prev.incluir_instructor_ficha:
                u = _instructor_user(apre)
                if u:
                    extras.append(u)
            ctx = {
                'nombre': f'{apre.perfil.nom} {apre.perfil.apelli}'.strip(),
                'dni': apre.perfil.dni,
                'dias': regla_prev.dias_umbral,
            }
            total += emitir_alerta(
                regla=regla_prev, origen_id=apre.id, contexto=ctx,
                destinatarios_extra=extras,
            )

    # Día 0
    regla_dia0 = T_alerta_regla.objects.filter(
        tipo='mayoria_edad_dia0', activa=True
    ).first()
    if regla_dia0:
        for apre in aprendices_para_alerta(0):
            _asegurar_carpeta_cc(apre)
            extras = []
            if regla_dia0.incluir_instructor_ficha:
                u = _instructor_user(apre)
                if u:
                    extras.append(u)
            ctx = {
                'nombre': f'{apre.perfil.nom} {apre.perfil.apelli}'.strip(),
                'dni': apre.perfil.dni,
                'dias': 0,
            }
            total += emitir_alerta(
                regla=regla_dia0, origen_id=apre.id, contexto=ctx,
                destinatarios_extra=extras,
            )

    # Riesgo (cumplió 18 hace N o más días sin CC actualizado)
    regla_riesgo = T_alerta_regla.objects.filter(
        tipo='mayoria_edad_riesgo', activa=True
    ).first()
    if regla_riesgo:
        from commons.models import T_apre
        from datetime import timedelta
        from django.utils import timezone

        hoy = timezone.localdate()
        limite = hoy - timedelta(days=18 * 365 + regla_riesgo.dias_umbral)
        candidatos = T_apre.objects.select_related('perfil', 'ficha__instru__perfil__user').filter(
            esta='activo', perfil__fecha_naci__lte=limite,
        )
        for apre in candidatos:
            d = dias_para_18(apre)
            if d is None or d > -regla_riesgo.dias_umbral:
                continue
            if tiene_cc_actualizado(apre):
                continue
            ctx = {
                'nombre': f'{apre.perfil.nom} {apre.perfil.apelli}'.strip(),
                'dni': apre.perfil.dni,
                'dias': abs(d),
            }
            total += emitir_alerta(
                regla=regla_riesgo, origen_id=apre.id, contexto=ctx,
            )

    logger.info('seguimiento_mayoria_edad: %s notificaciones emitidas', total)
    return total
