from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask


PROGRAMACIONES = [
    {
        'name': 'evaluar_inactividad_instructores_diario',
        'task': 'tasks.evaluar_inactividad_instructores',
        'cron': {'minute': '0', 'hour': '7', 'day_of_week': '*',
                 'day_of_month': '*', 'month_of_year': '*'},
    },
    {
        'name': 'seguimiento_mayoria_edad_diario',
        'task': 'tasks.seguimiento_mayoria_edad',
        'cron': {'minute': '15', 'hour': '7', 'day_of_week': '*',
                 'day_of_month': '*', 'month_of_year': '*'},
    },
]


class Command(BaseCommand):
    help = 'Crea o actualiza las tareas periódicas de Celery Beat (idempotente).'

    def handle(self, *args, **options):
        for cfg in PROGRAMACIONES:
            cron, _ = CrontabSchedule.objects.get_or_create(**cfg['cron'])
            obj, created = PeriodicTask.objects.update_or_create(
                name=cfg['name'],
                defaults={'task': cfg['task'], 'crontab': cron, 'enabled': True},
            )
            label = 'Creada' if created else 'Actualizada'
            self.stdout.write(self.style.SUCCESS(f'{label}: {obj.name} ({obj.task})'))
