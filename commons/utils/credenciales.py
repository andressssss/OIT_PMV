"""Helper para enviar credenciales de acceso a usuarios recién creados.

Se invoca desde la signal `usuarios/signals.py` (post_save de T_perfil) para
automatizar el envío. Si el envío falla, NUNCA propaga la excepción: solo
loguea un warning, para no interrumpir el flujo de creación del usuario.
"""
import logging

from commons.utils.email import enviar_correo

logger = logging.getLogger(__name__)


def enviar_credenciales(user, password_plain, perfil=None):
    """Envía al usuario sus credenciales (username + contraseña inicial) por correo.

    Args:
        user: instancia de User de Django.
        password_plain: contraseña en texto plano (lo que el usuario va a teclear).
        perfil: instancia opcional de T_perfil. Si viene, usamos perfil.mail
                como destinatario; si no, usamos user.email.

    Returns:
        True si se envió, False si no había email o falló el envío.
    """
    # Resolver destinatario: priorizamos perfil.mail; si no, user.email
    destinatario = None
    if perfil is not None:
        destinatario = getattr(perfil, 'mail', None)
    if not destinatario:
        destinatario = getattr(user, 'email', None)

    if not destinatario:
        logger.warning(
            "No se enviaron credenciales a usuario %s (id=%s): sin email registrado.",
            user.username, user.id,
        )
        return False

    # Saludo personalizado si tenemos perfil
    nombre = ''
    if perfil is not None:
        nombre = f"{perfil.nom or ''} {perfil.apelli or ''}".strip()
    saludo = f"Hola {nombre}," if nombre else "Hola,"

    asunto = "Bienvenido a la plataforma OIT - Credenciales de acceso"
    mensaje = (
        f"{saludo}<br><br>"
        f"Su cuenta en la plataforma institucional de Formación Profesional OIT "
        f"ha sido creada con éxito.<br><br>"
        f"<b>Sus datos de acceso son:</b><br>"
        f"Usuario: <b>{user.username}</b><br>"
        f"Contraseña inicial: <b>{password_plain}</b><br><br>"
        f"Por motivos de seguridad, le recomendamos cambiar su contraseña "
        f"al ingresar por primera vez."
    )

    try:
        enviar_correo(
            destinatarios=[destinatario],
            asunto=asunto,
            mensaje=mensaje,
        )
        logger.info(
            "Credenciales enviadas a %s (usuario=%s).", destinatario, user.username,
        )
        return True
    except Exception:
        logger.exception(
            "Error enviando credenciales a %s (usuario=%s).",
            destinatario, user.username,
        )
        return False