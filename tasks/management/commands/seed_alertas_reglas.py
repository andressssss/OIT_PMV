from django.core.management.base import BaseCommand

from tasks.models import T_alerta_regla


REGLAS = [
    {
        'tipo': 'inactividad_preventiva',
        'nivel': 'preventiva',
        'dias_umbral': 3,
        'asunto_correo': 'Alerta preventiva: instructor {nombre} sin actividad ({dias} días)',
        'plantilla_mensaje': (
            'El instructor {nombre} (DNI {dni}) no registra actividad en la '
            'plataforma desde hace {dias} días. Esta es una alerta preventiva.'
        ),
    },
    {
        'tipo': 'inactividad_seguimiento',
        'nivel': 'seguimiento',
        'dias_umbral': 6,
        'asunto_correo': 'Alerta de seguimiento: instructor {nombre} inactivo ({dias} días)',
        'plantilla_mensaje': (
            'El instructor {nombre} (DNI {dni}) no registra actividad en la '
            'plataforma desde hace {dias} días. Requiere seguimiento.'
        ),
    },
    {
        'tipo': 'mayoria_edad_preventiva',
        'nivel': 'preventiva',
        'dias_umbral': 30,
        'incluir_instructor_ficha': True,
        'asunto_correo': 'Aprendiz {nombre} cumple 18 años en {dias} días',
        'plantilla_mensaje': (
            'El aprendiz {nombre} (DNI {dni}) cumplirá 18 años en {dias} días. '
            'Por favor solicitar el documento de cédula de ciudadanía actualizado.'
        ),
    },
    {
        'tipo': 'mayoria_edad_dia0',
        'nivel': 'seguimiento',
        'dias_umbral': 0,
        'incluir_instructor_ficha': True,
        'asunto_correo': 'Aprendiz {nombre} cumple 18 años hoy',
        'plantilla_mensaje': (
            'El aprendiz {nombre} (DNI {dni}) cumple 18 años hoy. '
            'Solicitar la cédula de ciudadanía actualizada y cargarla al portafolio.'
        ),
    },
    {
        'tipo': 'mayoria_edad_riesgo',
        'nivel': 'riesgo',
        'dias_umbral': 30,
        'asunto_correo': 'Riesgo: aprendiz {nombre} sin actualizar CC ({dias} días)',
        'plantilla_mensaje': (
            'El aprendiz {nombre} (DNI {dni}) cumplió 18 años hace {dias} días '
            'y aún no se ha cargado la cédula de ciudadanía actualizada en el portafolio.'
        ),
    },
]


class Command(BaseCommand):
    help = 'Crea las reglas de alerta iniciales si no existen (idempotente).'

    def handle(self, *args, **options):
        creadas = 0
        existentes = 0
        for cfg in REGLAS:
            obj, created = T_alerta_regla.objects.get_or_create(
                tipo=cfg['tipo'],
                defaults={k: v for k, v in cfg.items() if k != 'tipo'},
            )
            if created:
                creadas += 1
                self.stdout.write(self.style.SUCCESS(f'Creada: {obj.tipo}'))
            else:
                existentes += 1
                self.stdout.write(f'Ya existe: {obj.tipo}')
        self.stdout.write(self.style.SUCCESS(
            f'Resumen: {creadas} creadas, {existentes} existentes.'
        ))
