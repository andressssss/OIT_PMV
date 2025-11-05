from django.core.management.base import BaseCommand
from django.db import transaction
from commons.models import T_apre, T_DocumentFolderAprendiz


@transaction.atomic
def limpiar_hijos_de_carpeta(carpeta_padre, command):
    """
    Si la carpeta padre tiene hijos de tipo 'carpeta',
    reasigna sus hijos (nietos) directamente a la carpeta padre
    y luego elimina las carpetas hijas originales.
    """
    hijos = carpeta_padre.children.filter(tipo="carpeta")

    if not hijos.exists():
        command.stdout.write(command.style.WARNING(
            f"No se encontraron carpetas hijas bajo '{carpeta_padre.name}' (ID: {carpeta_padre.id})"
        ))
        return

    for hijo in hijos:
        # Reasignar los hijos del hijo al padre original
        nietos = hijo.children.all()
        for nieto in nietos:
            nieto.parent = carpeta_padre
            nieto.save(update_fields=["parent"])
            command.stdout.write(command.style.SUCCESS(
                f"Reasignado: '{nieto.name}' → nuevo padre '{carpeta_padre.name}'"
            ))

        # Eliminar la carpeta hija original
        hijo.delete()
        command.stdout.write(command.style.WARNING(
            f"Eliminada carpeta hija: '{hijo.name}' (ID: {hijo.id})"
        ))

    command.stdout.write(command.style.SUCCESS(
        f"✔ Limpieza completada para '{carpeta_padre.name}' (ID: {carpeta_padre.id})"
    ))


class Command(BaseCommand):
    help = (
        "Si una carpeta padre específica tiene subcarpetas, "
        "sus hijos son reasignados al padre y las subcarpetas se eliminan."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--id_carpeta",
            type=int,
            help="ID de la carpeta padre sobre la cual se ejecutará la limpieza.",
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

        self.stdout.write(self.style.WARNING(
            f"Iniciando limpieza bajo '{carpeta_padre.name}' (ID: {carpeta_padre.id})"
        ))

        limpiar_hijos_de_carpeta(carpeta_padre, self)
