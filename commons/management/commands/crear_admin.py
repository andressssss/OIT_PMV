from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from commons.models import T_perfil, T_admin
from commons.management.commands.poblar_permisos import crear_permisos


class Command(BaseCommand):
    help = "Crea un usuario administrador con perfil y registro en t_admin"

    def add_arguments(self, parser):
        parser.add_argument("--username", type=str, required=True)
        parser.add_argument("--password", type=str, required=True)
        parser.add_argument("--email", type=str, required=True)
        parser.add_argument("--nom", type=str, required=True, help="Nombre")
        parser.add_argument("--apelli", type=str, required=True, help="Apellido")
        parser.add_argument("--dni", type=int, required=True, help="Numero de documento")
        parser.add_argument("--tipo_dni", type=str, default="cc",
                            choices=["ti", "cc", "pp", "ce", "ppt"])
        parser.add_argument("--tele", type=str, default="0000000000")
        parser.add_argument("--dire", type=str, default="N/A")
        parser.add_argument("--gene", type=str, default="H", choices=["H", "M"])
        parser.add_argument("--area", type=str, default="sistemas",
                            choices=["sistemas", "contable", "direccion", "rrhh"])

    def handle(self, *args, **options):
        username = options["username"]

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(
                f"El usuario '{username}' ya existe"
            ))
            return

        user = User.objects.create_superuser(
            username=username,
            email=options["email"],
            password=options["password"],
        )

        perfil = T_perfil.objects.create(
            user=user,
            nom=options["nom"],
            apelli=options["apelli"],
            tipo_dni=options["tipo_dni"],
            dni=options["dni"],
            tele=options["tele"],
            dire=options["dire"],
            mail=options["email"],
            gene=options["gene"],
            rol="admin",
        )

        T_admin.objects.create(
            perfil=perfil,
            area=options["area"],
            esta="activo",
        )

        crear_permisos(perfil)

        self.stdout.write(self.style.SUCCESS(
            f"Admin '{username}' creado con perfil, registro admin y permisos"
        ))
