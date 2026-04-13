from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from commons.models import T_PlantillaAdmin


class Command(BaseCommand):
    help = "Agrega un usuario a la lista de administradores de plantillas"

    def add_arguments(self, parser):
        parser.add_argument("--username", type=str, required=True)

    def handle(self, *args, **options):
        username = options["username"]
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"No existe el usuario '{username}'"))
            return

        admin, created = T_PlantillaAdmin.objects.get_or_create(user=user)
        if created:
            self.stdout.write(self.style.SUCCESS(f"'{username}' agregado como admin de plantillas"))
        else:
            self.stdout.write(self.style.WARNING(f"'{username}' ya es admin de plantillas"))
