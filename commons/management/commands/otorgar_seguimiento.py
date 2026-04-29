from django.core.management.base import BaseCommand, CommandError

from commons.models import T_perfil, T_permi


class Command(BaseCommand):
    help = (
        "Otorga el permiso (seguimiento, ver) a un perfil específico. "
        "Útil para probar el módulo solo con tu usuario antes de poblárselo a todos."
    )

    def add_arguments(self, parser):
        grp = parser.add_mutually_exclusive_group(required=True)
        grp.add_argument('--username', type=str, help='Nombre de usuario Django')
        grp.add_argument('--dni', type=str, help='DNI del perfil')
        grp.add_argument('--perfil_id', type=int, help='ID de T_perfil')
        parser.add_argument(
            '--revocar', action='store_true',
            help='Si está presente, elimina el permiso en lugar de crearlo.',
        )

    def handle(self, *args, **opts):
        qs = T_perfil.objects.all()
        if opts['username']:
            qs = qs.filter(user__username=opts['username'])
        elif opts['dni']:
            qs = qs.filter(dni=opts['dni'])
        elif opts['perfil_id']:
            qs = qs.filter(id=opts['perfil_id'])

        perfil = qs.first()
        if not perfil:
            raise CommandError('Perfil no encontrado.')

        if opts['revocar']:
            n = T_permi.objects.filter(
                perfil=perfil, modu='seguimiento', acci='ver'
            ).delete()[0]
            self.stdout.write(self.style.WARNING(
                f'Revocado seguimiento.ver de {perfil} (afectados: {n}).'
            ))
            return

        obj, created = T_permi.objects.get_or_create(
            perfil=perfil, modu='seguimiento', acci='ver',
            defaults={'filtro': None},
        )
        if created:
            self.stdout.write(self.style.SUCCESS(
                f'OK: {perfil} ahora tiene seguimiento.ver.'
            ))
        else:
            self.stdout.write(f'Sin cambios: {perfil} ya tenía el permiso.')
