import logging
from datetime import timedelta

from django.utils import timezone

from commons.utils.email import enviar_correo
from tasks.models import T_notifi, T_alerta_regla


logger = logging.getLogger(__name__)


def _render(template: str, contexto: dict) -> str:
    if not template:
        return ''
    try:
        return template.format(**contexto)
    except (KeyError, IndexError) as e:
        logger.warning('Falta variable en plantilla: %s', e)
        return template


def emitir_alerta(
    regla: T_alerta_regla,
    origen_id: int,
    contexto: dict,
    destinatarios_extra=None,
    url: str = '',
) -> int:
    """Crea T_notifi y envía correos según la regla. Idempotente para el día:
    no duplica notificaciones ya emitidas del mismo `origen_tipo`+`origen_id`+usuario
    en las últimas 24 horas.

    `contexto` debe incluir variables para la plantilla: nombre, dni, dias.
    `destinatarios_extra` es una iterable opcional de `User` (ej. instructor de ficha).
    Retorna el número de notificaciones emitidas.
    """
    if not regla.activa:
        return 0

    asunto = _render(regla.asunto_correo, contexto) or regla.get_tipo_display()
    mensaje = _render(regla.plantilla_mensaje, contexto)
    origen_tipo = regla.tipo

    usuarios = []
    for perfil in regla.destinatarios.select_related('user').all():
        if perfil.user:
            usuarios.append(perfil.user)
    if destinatarios_extra:
        usuarios.extend(destinatarios_extra)

    seen = set()
    usuarios_unicos = []
    for u in usuarios:
        if u and u.id not in seen:
            seen.add(u.id)
            usuarios_unicos.append(u)

    if not usuarios_unicos:
        logger.info('Regla %s sin destinatarios resolubles', regla.tipo)
        return 0

    desde = timezone.now() - timedelta(hours=24)
    emitidas = 0
    correos_pendientes = []

    for user in usuarios_unicos:
        ya_emitida = T_notifi.objects.filter(
            usuario=user,
            origen_tipo=origen_tipo,
            origen_id=origen_id,
            creada_en__gte=desde,
        ).exists()
        if ya_emitida:
            continue

        if regla.enviar_notificacion:
            T_notifi.objects.create(
                usuario=user,
                titulo=asunto,
                mensaje=mensaje,
                nivel=regla.nivel,
                url=url or None,
                origen_tipo=origen_tipo,
                origen_id=origen_id,
            )
            emitidas += 1

        if regla.enviar_correo:
            mail = getattr(getattr(user, 'perfil', None), 'mail', None) or user.email
            if mail:
                correos_pendientes.append(mail)

    if correos_pendientes:
        try:
            enviar_correo(
                destinatarios=correos_pendientes,
                asunto=asunto,
                mensaje=mensaje,
            )
        except Exception:
            logger.exception('Error enviando correo de regla %s', regla.tipo)

    return emitidas
