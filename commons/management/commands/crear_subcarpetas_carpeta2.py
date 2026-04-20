from django.core.management.base import BaseCommand
from commons.models import T_DocumentFolderAprendiz

NOMBRE_CARPETA_2 = "2. PLANEACION SEGUIMIENTO Y EVALUACION ETAPA PRODUCTIVA"

SUBCARPETAS = [
    "EVIDENCIAS PROYECTO PRODUCTIVO",
    "GFPI-F-023-PLANEACIÓN, SEGUIMIENTO Y EVALUACIÓN ETAPA PRODUCTIVA",
    "GFPI-F-147-BITÁCORAS SEGUIMIENTO ETAPA PRODUCTIVA",
    "GFPI-F-165-V4-INSCRIPCIÓN A ETAPA PRODUCTIVA",
    "PROCESO DE CERTIFICACIÓN",
]


def get_carpetas_sin_hijos(id_aprendiz=None):
    """Retorna las carpetas 2 que no tienen subcarpetas."""
    qs = T_DocumentFolderAprendiz.objects.filter(
        name=NOMBRE_CARPETA_2,
        tipo="carpeta",
    ).select_related("aprendiz__ficha")

    if id_aprendiz:
        qs = qs.filter(aprendiz__id=id_aprendiz)

    return [c for c in qs if not c.get_children().exists()]


class Command(BaseCommand):
    help = "Crea las subcarpetas faltantes en la carpeta 2 de aprendices existentes"

    def add_arguments(self, parser):
        parser.add_argument(
            "--id_aprendiz",
            type=int,
            help="ID de un aprendiz específico para procesar",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Solo muestra qué carpetas serían afectadas, sin escribir en BD",
        )

    def handle(self, *args, **options):
        id_aprendiz = options.get("id_aprendiz")
        dry_run = options.get("dry_run")

        carpetas = get_carpetas_sin_hijos(id_aprendiz)

        if not carpetas:
            self.stdout.write(self.style.SUCCESS("No hay carpetas afectadas."))
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"DRY RUN — {len(carpetas)} carpeta(s) serían afectadas:\n"
                )
            )
            self.stdout.write(
                f"{'ID carpeta':<12} {'Aprendiz ID':<14} {'Ficha':<12} Nombre carpeta"
            )
            self.stdout.write("-" * 70)
            for c in carpetas:
                ficha_num = c.aprendiz.ficha.num if c.aprendiz.ficha else "Sin ficha"
                self.stdout.write(
                    f"{c.id:<12} {c.aprendiz.id:<14} {ficha_num:<12} {c.name}"
                )
            self.stdout.write(
                f"\nSubcarpetas que se crearían por carpeta: {len(SUBCARPETAS)}"
            )
            self.stdout.write(
                f"Total subcarpetas a crear: {len(carpetas) * len(SUBCARPETAS)}"
            )
            return

        creadas_total = 0
        existentes_total = 0

        for carpeta in carpetas:
            for nombre in SUBCARPETAS:
                _, created = T_DocumentFolderAprendiz.objects.get_or_create(
                    name=nombre,
                    tipo="carpeta",
                    aprendiz=carpeta.aprendiz,
                    parent=carpeta,
                )
                if created:
                    creadas_total += 1
                else:
                    existentes_total += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"[aprendiz {carpeta.aprendiz.id}] Subcarpetas procesadas."
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nListo. Creadas: {creadas_total} | Ya existían: {existentes_total}"
            )
        )
