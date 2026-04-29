from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class T_notifi(models.Model):
    NIVEL_CHOICES = [
        ('info', 'Información'),
        ('preventiva', 'Preventiva'),
        ('seguimiento', 'Seguimiento'),
        ('riesgo', 'Riesgo'),
    ]

    usuario = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='notificaciones'
    )
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField(blank=True)
    nivel = models.CharField(
        max_length=20, choices=NIVEL_CHOICES, default='info'
    )
    url = models.CharField(max_length=500, blank=True, null=True)
    leida = models.BooleanField(default=False)
    leida_en = models.DateTimeField(null=True, blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    # Origen genérico (qué proceso la generó)
    origen_tipo = models.CharField(max_length=50, blank=True, null=True)
    origen_id = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 't_notifi'
        ordering = ['-creada_en']
        indexes = [
            models.Index(fields=['usuario', 'leida']),
            models.Index(fields=['origen_tipo', 'origen_id']),
        ]

    def __str__(self):
        return f"[{self.nivel}] {self.titulo} -> {self.usuario.username}"

    def marcar_leida(self):
        if not self.leida:
            self.leida = True
            self.leida_en = timezone.now()
            self.save(update_fields=['leida', 'leida_en'])


class T_alerta_regla(models.Model):
    TIPO_CHOICES = [
        ('inactividad_preventiva', 'Inactividad - Preventiva'),
        ('inactividad_seguimiento', 'Inactividad - Seguimiento'),
        ('mayoria_edad_preventiva', 'Mayoría de edad - 30 días antes'),
        ('mayoria_edad_dia0', 'Mayoría de edad - Día del cumpleaños'),
        ('mayoria_edad_riesgo', 'Mayoría de edad - Riesgo (CC sin actualizar)'),
    ]

    NIVEL_CHOICES = T_notifi.NIVEL_CHOICES

    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, unique=True)
    nivel = models.CharField(
        max_length=20, choices=NIVEL_CHOICES, default='preventiva'
    )
    activa = models.BooleanField(default=True)
    dias_umbral = models.IntegerField(
        help_text="Días para activar la regla (positivo o negativo según el tipo)"
    )

    destinatarios = models.ManyToManyField(
        'commons.T_perfil',
        blank=True,
        related_name='alertas_destino',
        help_text="Perfiles que reciben la notificación/correo (admin, líder, gestor, etc.)",
    )
    incluir_instructor_ficha = models.BooleanField(
        default=False,
        help_text="Si está activo, también notifica al instructor de la ficha del aprendiz (sólo aplica a reglas de mayoría de edad)",
    )

    enviar_correo = models.BooleanField(default=True)
    enviar_notificacion = models.BooleanField(default=True)

    asunto_correo = models.CharField(
        max_length=200, blank=True,
        help_text="Plantilla. Variables disponibles: {nombre}, {dni}, {dias}",
    )
    plantilla_mensaje = models.TextField(
        blank=True,
        help_text="Plantilla del cuerpo. Variables: {nombre}, {dni}, {dias}, {url}",
    )

    notas = models.TextField(blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 't_alerta_regla'
        verbose_name = 'Regla de alerta'
        verbose_name_plural = 'Reglas de alerta'

    def __str__(self):
        return f"{self.get_tipo_display()} ({'activa' if self.activa else 'inactiva'})"
