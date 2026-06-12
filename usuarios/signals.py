"""Signals de la app usuarios.

Centraliza los efectos colaterales que deben dispararse cuando se crea un
perfil de usuario o se reactiva una cuenta, sin necesidad de modificar cada
view de creación una por una.

La signal está registrada en `usuarios/apps.py` (método `ready`).
"""

import logging

from django.contrib.auth import get_user_model
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from commons.models import T_perfil
from commons.utils.credenciales import enviar_credenciales

logger = logging.getLogger(__name__)

User = get_user_model()


# ─── Signal 1: Envío de credenciales al CREAR un perfil ────────────────────

@receiver(post_save, sender=T_perfil)
def enviar_credenciales_al_crear_perfil(sender, instance, created, **kwargs):
    """Cuando se crea un perfil nuevo con User asociado, le envía sus
    credenciales. Convención: la contraseña inicial es el DNI del perfil."""

    if not created:
        return

    user = getattr(instance, 'user', None)
    if not user:
        return

    dni = getattr(instance, 'dni', None)
    if not dni:
        logger.warning(
            "Perfil %s creado sin DNI; no se pueden inferir credenciales.",
            instance.id,
        )
        return

    enviar_credenciales(user, str(dni), perfil=instance)


# ─── Signal 2: Envío de credenciales al REACTIVAR un usuario ───────────────

@receiver(pre_save, sender=User)
def _guardar_is_active_anterior(sender, instance, **kwargs):
    """Antes de guardar el User, almacena el valor anterior de is_active
    para que el post_save pueda detectar reactivaciones."""

    if instance.pk:
        try:
            instance._old_is_active = (
                User.objects.filter(pk=instance.pk)
                .values_list('is_active', flat=True)
                .first()
            )
        except Exception:
            instance._old_is_active = None
    else:
        instance._old_is_active = None


@receiver(post_save, sender=User)
def enviar_credenciales_al_reactivar(sender, instance, created, **kwargs):
    """Cuando is_active cambia de False a True (reactivación), resetea la
    contraseña al DNI del perfil y envía las credenciales por correo."""

    if created:
        # La creación se maneja en la signal de T_perfil.
        return

    old_active = getattr(instance, '_old_is_active', None)

    if old_active is not False or not instance.is_active:
        # No es una reactivación (False → True).
        return

    # ── Reactivación detectada ──
    try:
        perfil = T_perfil.objects.get(user=instance)
    except T_perfil.DoesNotExist:
        logger.warning(
            "User %s reactivado pero no tiene T_perfil asociado.",
            instance.username,
        )
        return

    dni = getattr(perfil, 'dni', None)
    if not dni:
        logger.warning(
            "User %s reactivado sin DNI en perfil; no se envían credenciales.",
            instance.username,
        )
        return

    # Resetear contraseña al DNI (sin disparar save recursivo).
    instance.set_password(str(dni))
    User.objects.filter(pk=instance.pk).update(password=instance.password)

    enviar_credenciales(instance, str(dni), perfil=perfil)
    logger.info(
        "Usuario %s reactivado: contraseña reseteada a DNI y credenciales enviadas.",
        instance.username,
    )
