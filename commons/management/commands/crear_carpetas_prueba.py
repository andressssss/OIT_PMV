from django.core.management.base import BaseCommand
from django.db import transaction
from commons.models import T_DocumentFolderAprendiz


@transaction.atomic
def crear_carpetas_prueba(carpeta_padre, command):
    """
    Crea tres carpetas hijas dentro de la carpeta especificada.
    """
    nombres = [
        "Carpeta Prueba 1",
        "Carpeta Prueba 2",
        "Carpeta Prueba 3",
    ]

    for nombre in nombres:
        carpeta = T_DocumentFolderAprendiz.objects.create(
            name=nombre,
            tipo="carpeta",
            aprendiz=carpeta_padre.aprendiz,
            parent=carpeta_padre,
        )
        command.stdout.write(
            command.style.SUCCESS(
                f"✅ Carpeta creada: '{carpeta.name}' (ID: {carpeta.id}) bajo '{carpeta_padre.name}'"
            )
        )


class Command(BaseCommand):
    help = "Crea 3 carpetas de prueba como hijas de una carpeta existente."

    def add_arguments(self, parser):
        parser.add_argument(
            "--id_carpeta",
            type=int,
            help="ID de la carpeta padre existente donde se crearán las carpetas de prueba.",
        )

    def handle(self, *args, **options):
        id_carpeta = options.get("id_carpeta")

        if not id_carpeta:
            self.stdout.write(self.style.ERROR("Debe especificar --id_carpeta"))
            return

        try:
            carpeta_padre = T_DocumentFolderAprendiz.objects.get(id=id_carpeta)
        except T_DocumentFolderAprendiz.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"No existe carpeta con id {id_carpeta}"))
            return

        self.stdout.write(
            self.style.WARNING(
                f"Creando carpetas de prueba bajo '{carpeta_padre.name}' (ID: {carpeta_padre.id})"
            )
        )

        crear_carpetas_prueba(carpeta_padre, self)
