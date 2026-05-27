"""Signals de la app usuarios.

Centraliza los efectos colaterales que deben dispararse cuando se crea un
perfil de usuario, sin necesidad de modificar cada view de creación una por
una. La signal está registrada en `usuarios/apps.py` (método `ready`).
"""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from commons.models import T_perfil
from commons.utils.credenciales import enviar_credenciales

logger = logging.getLogger(__name__)


@receiver(post_save, sender=T_perfil)
def enviar_credenciales_al_crear_perfil(sender, instance, created, **kwargs):
    """Cuando se crea un perfil nuevo con User asociado, le envía sus credenciales.

    Convención actual del proyecto: la contraseña inicial es el DNI del perfil.
    Si esa convención cambia en el futuro (por ejemplo, generar contraseñas
    aleatorias), actualizar el valor que se pasa a `enviar_credenciales`.
    """
    if not created:
        # Solo nos interesa la creación, no las modificaciones posteriores.
        return

    user = getattr(instance, 'user', None)
    if not user:
        # Perfil creado sin user asociado; no hay credenciales que enviar.
        return

    dni = getattr(instance, 'dni', None)
    if not dni:
        logger.warning(
            "Perfil %s creado sin DNI; no se pueden inferir credenciales.",
            instance.id,
        )
        return

    enviar_credenciales(user, str(dni), perfil=instance)