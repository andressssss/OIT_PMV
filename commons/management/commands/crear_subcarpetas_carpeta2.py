from django.core.management.base import BaseCommand
from django.db import transaction
from commons.models import T_apre, T_DocumentFolderAprendiz

NOMBRE_CARPETA_2 = "2. PLANEACION SEGUIMIENTO Y EVALUACION ETAPA PRODUCTIVA"

SUB_INSCRIPCION_V4 = "GFPI-F-165-V4-INSCRIPCIÓN A ETAPA PRODUCTIVA"
SUB_INSCRIPCION_V3 = "GFPI-F-165-V3-INSCRIPCIÓN A ETAPA PRODUCTIVA"

SUBCARPETAS = [
    "EVIDENCIAS PROYECTO PRODUCTIVO",
    "GFPI-F-023-PLANEACIÓN, SEGUIMIENTO Y EVALUACIÓN ETAPA PRODUCTIVA",
    "GFPI-F-147-BITÁCORAS SEGUIMIENTO ETAPA PRODUCTIVA",
    SUB_INSCRIPCION_V4,
    "PROCESO DE CERTIFICACIÓN",
]


def asegurar_carpeta_2(aprendiz, dry_run=False):
    """
    Garantiza que el aprendiz tenga la carpeta 2 y sus 5 subcarpetas.
    Si la subcarpeta de inscripción existe como V3, la renombra a V4.
    Retorna dict con contadores: padre_creada, subs_creadas, subs_existentes, v3_renombradas, conflictos.
    """
    stats = {
        "padre_creada": False,
        "subs_creadas": 0,
        "subs_existentes": 0,
        "v3_renombradas": 0,
        "conflictos": [],
    }

    if dry_run:
        padre = T_DocumentFolderAprendiz.objects.filter(
            name=NOMBRE_CARPETA_2, tipo="carpeta",
            aprendiz=aprendiz, parent=None,
        ).first()
        stats["padre_creada"] = padre is None
    else:
        padre, creada = T_DocumentFolderAprendiz.objects.get_or_create(
            name=NOMBRE_CARPETA_2, tipo="carpeta",
            aprendiz=aprendiz, parent=None,
        )
        stats["padre_creada"] = creada

    # Si no hay padre real todavía (dry run sin carpeta 2), las subs también faltarían todas.
    if padre is None:
        stats["subs_creadas"] = len(SUBCARPETAS)
        return stats

    hijos_qs = T_DocumentFolderAprendiz.objects.filter(
        aprendiz=aprendiz, parent=padre, tipo="carpeta",
    )

    v3 = hijos_qs.filter(name=SUB_INSCRIPCION_V3).first()
    v4 = hijos_qs.filter(name=SUB_INSCRIPCION_V4).first()

    if v3 and v4:
        stats["conflictos"].append(
            f"aprendiz {aprendiz.id}: coexisten V3 (id={v3.id}) y V4 (id={v4.id}); no se toca"
        )
    elif v3 and not v4:
        if not dry_run:
            v3.name = SUB_INSCRIPCION_V4
            v3.save(update_fields=["name"])
        stats["v3_renombradas"] = 1

    for nombre in SUBCARPETAS:
        # La de inscripción V4 ya quedó resuelta arriba (rename o existente).
        if nombre == SUB_INSCRIPCION_V4:
            if v3 or v4:
                stats["subs_existentes"] += 1
                continue

        if dry_run:
            existe = hijos_qs.filter(name=nombre).exists()
            if existe:
                stats["subs_existentes"] += 1
            else:
                stats["subs_creadas"] += 1
        else:
            _, created = T_DocumentFolderAprendiz.objects.get_or_create(
                name=nombre, tipo="carpeta",
                aprendiz=aprendiz, parent=padre,
            )
            if created:
                stats["subs_creadas"] += 1
            else:
                stats["subs_existentes"] += 1

    return stats


class Command(BaseCommand):
    help = (
        "Garantiza que todos los aprendices tengan la carpeta 2 "
        "(PLANEACION SEGUIMIENTO Y EVALUACION ETAPA PRODUCTIVA) y sus 5 subcarpetas. "
        "Renombra GFPI-F-165-V3 a V4 cuando corresponda."
    )

    def add_arguments(self, parser):
        parser.add_argument("--id_aprendiz", type=int, help="Procesar solo un aprendiz")
        parser.add_argument("--id_ficha", type=int, help="Procesar solo aprendices de una ficha")
        parser.add_argument("--dry-run", action="store_true", help="Simula sin escribir en BD")

    def handle(self, *args, **options):
        id_aprendiz = options.get("id_aprendiz")
        id_ficha = options.get("id_ficha")
        dry_run = options.get("dry_run")

        qs = T_apre.objects.all()
        if id_aprendiz:
            qs = qs.filter(id=id_aprendiz)
        if id_ficha:
            qs = qs.filter(ficha_id=id_ficha)

        total = qs.count()
        if not total:
            self.stdout.write(self.style.WARNING("No hay aprendices para procesar."))
            return

        self.stdout.write(
            f"{'[DRY RUN] ' if dry_run else ''}Procesando {total} aprendiz(es)..."
        )

        padres_creados = 0
        subs_creadas = 0
        subs_existentes = 0
        v3_renombradas = 0
        conflictos = []

        for aprendiz in qs.iterator():
            if dry_run:
                stats = asegurar_carpeta_2(aprendiz, dry_run=True)
            else:
                with transaction.atomic():
                    stats = asegurar_carpeta_2(aprendiz, dry_run=False)

            if stats["padre_creada"]:
                padres_creados += 1
            subs_creadas += stats["subs_creadas"]
            subs_existentes += stats["subs_existentes"]
            v3_renombradas += stats["v3_renombradas"]
            conflictos.extend(stats["conflictos"])

        self.stdout.write(self.style.SUCCESS(
            f"\nResumen{' (DRY RUN)' if dry_run else ''}:\n"
            f"  Aprendices procesados: {total}\n"
            f"  Carpetas 2 creadas: {padres_creados}\n"
            f"  Subcarpetas creadas: {subs_creadas}\n"
            f"  Subcarpetas ya existentes: {subs_existentes}\n"
            f"  V3 renombradas a V4: {v3_renombradas}\n"
            f"  Conflictos V3+V4: {len(conflictos)}"
        ))

        if conflictos:
            self.stdout.write(self.style.WARNING("\nConflictos a revisar manualmente:"))
            for msg in conflictos:
                self.stdout.write(f"  - {msg}")
