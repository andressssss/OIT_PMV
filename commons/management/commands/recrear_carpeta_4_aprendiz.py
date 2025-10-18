from django.core.management.base import BaseCommand
from commons.models import T_apre, T_DocumentFolderAprendiz, T_fase, T_raps

FASES_LABELS = {
    "ANALISIS": "1. ANÁLISIS",
    "PLANEACION": "2. PLANEACIÓN",
    "EJECUCION": "3. EJECUCIÓN",
    "EVALUACION": "4. EVALUACIÓN"
}


def recrear_carpeta_evidencias(aprendiz):
    """Elimina y recrea la carpeta 4. EVIDENCIAS DE APRENDIZAJE de un aprendiz"""

    # Buscar la carpeta padre
    carpeta, _ = T_DocumentFolderAprendiz.objects.get_or_create(
        name="4. EVIDENCIAS DE APRENDIZAJE",
        tipo="carpeta",
        aprendiz=aprendiz,
        parent=None
    )

    # Borrar todo lo que haya dentro
    T_DocumentFolderAprendiz.objects.filter(parent=carpeta).delete()

    # Crear fases
    fases = T_fase.objects.filter(nom__in=FASES_LABELS.keys()).order_by("id")

    for fase in fases:
        carpeta_fase, _ = T_DocumentFolderAprendiz.objects.get_or_create(
            name=FASES_LABELS.get(fase.nom.upper(), fase.nom),
            tipo="carpeta",
            aprendiz=aprendiz,
            parent=carpeta
        )

        # Carpeta fija en análisis
        if carpeta_fase.name == "1. ANÁLISIS":
            T_DocumentFolderAprendiz.objects.get_or_create(
                name="COMPETENCIA DE LA INDUCCIÓN",
                tipo="carpeta",
                aprendiz=aprendiz,
                parent=carpeta_fase
            )

        # Competencias y RAPs
        raps_fase = T_raps.objects.filter(
            progra=aprendiz.ficha.progra,
            fase=fase
        ).select_related("compe", "progra")

        competencias = {}
        for rap in raps_fase:
            competencias.setdefault(rap.compe, []).append(rap)

        for compe, raps in competencias.items():
            carpeta_compe, _ = T_DocumentFolderAprendiz.objects.get_or_create(
                name=f"COMPETENCIA {compe.cod} - {compe.nom}",
                tipo="carpeta",
                aprendiz=aprendiz,
                parent=carpeta_fase
            )
            for rap in raps:
                T_DocumentFolderAprendiz.objects.get_or_create(
                    name=rap.nom,
                    tipo="carpeta",
                    aprendiz=aprendiz,
                    parent=carpeta_compe
                )


class Command(BaseCommand):
    help = "Recrea desde cero la carpeta 4. EVIDENCIAS DE APRENDIZAJE para aprendices"

    def add_arguments(self, parser):
        parser.add_argument(
            "--id_aprendiz",
            type=int,
            help="ID de un aprendiz específico para actualizar"
        )
        
        parser.add_argument(
            "--id_ficha",
            type=int,
            help="ID de una ficha para actualizar"
        )

    def handle(self, *args, **options):
        id_aprendiz = options.get("id_aprendiz")
        id_ficha = options.get("id_ficha")
        if id_aprendiz:
            aprendices = T_apre.objects.filter(id=id_aprendiz)
            if not aprendices.exists():
                self.stdout.write(self.style.ERROR(
                    f"No se encontró el aprendiz con id={id_aprendiz}"
                ))
                return
        elif id_ficha:
            aprendices = T_apre.objects.filter(ficha__id=id_ficha)
            if not aprendices.exists():
                self.stdout.write(self.style.ERROR(
                    f"No se encontraron aprendices relacionados a la ficha={id_ficha}"
                ))
                return
        else:
            self.stdout.write("Por seguridad esta función requiere objetivar la muestra de aprendices, use algún parámetro")
            return

        for aprendiz in aprendices:
            if not aprendiz.ficha or not aprendiz.ficha.progra:
                self.stdout.write(
                    f"[{aprendiz.id}] No tiene ficha o programa asociado, se omite"
                )
                continue

            recrear_carpeta_evidencias(aprendiz)

            self.stdout.write(self.style.SUCCESS(
                f"[{aprendiz.id}] Carpeta 4 recreada correctamente"
            ))
