from django.core.management.base import BaseCommand
from commons.models import T_apre, T_DocumentFolderAprendiz, T_fase, T_raps
import unicodedata

estructura_documental_aprendiz = {
    "1. ACTA PLAN DE MEJORAMIENTO": {
        "1. ANÁLISIS": {},
        "2. PLANEACIÓN": {},
        "3. EJECUCIÓN": {},
        "4. EVALUACIÓN": {},
    },
    "2. PLANEACION SEGUIMIENTO Y EVALUACION ETAPA PRODUCTIVA": {},
    "3. GUIA DE APRENDIZAJE": {
        "1. ANÁLISIS": {
            "GUIAS DE LA FASE": {},
            "INSTRUMENTOS DE EVALUACION": {},
        },
        "2. PLANEACIÓN": {
            "GUIAS DE LA FASE": {},
            "INSTRUMENTOS DE EVALUACION": {},
        },
        "3. EJECUCIÓN": {
            "GUIAS DE LA FASE": {},
            "INSTRUMENTOS DE EVALUACION": {},
        },
        "4. EVALUACIÓN": {
            "GUIAS DE LA FASE": {},
            "INSTRUMENTOS DE EVALUACION": {},
        },
    },
    "4. EVIDENCIAS DE APRENDIZAJE": {},
    "5. PLAN DE TRABAJO CON SUS DESCRIPTORES": {
        "1. ANÁLISIS": {},
        "2. PLANEACIÓN": {},
        "3. EJECUCIÓN": {},
        "4. EVALUACIÓN": {},
    },
}

FASES_LABELS = {
    "ANALISIS": "1. ANÁLISIS",
    "PLANEACION": "2. PLANEACIÓN",
    "EJECUCION": "3. EJECUCIÓN",
    "EVALUACION": "4. EVALUACIÓN"
}


def crear_estructura_arbol_aprendiz(aprendiz, estructura, parent=None):
    """Crea estructura inicial de carpetas para un aprendiz."""
    for nombre, hijos in estructura.items():
        carpeta, _ = T_DocumentFolderAprendiz.objects.get_or_create(
            name=nombre,
            tipo="carpeta",
            aprendiz=aprendiz,
            parent=parent
        )

        if nombre == "4. EVIDENCIAS DE APRENDIZAJE":
            fases = T_fase.objects.filter(
                nom__in=FASES_LABELS.keys()
            ).order_by("id")

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

        elif hijos:
            crear_estructura_arbol_aprendiz(aprendiz, hijos, carpeta)


class Command(BaseCommand):
    help = "Crea o actualiza la estructura documental de aprendices"

    def add_arguments(self, parser):
        parser.add_argument(
            "--id_aprendiz",
            type=int,
            help="ID de un aprendiz específico para actualizar/crear portafolio"
        )

    def handle(self, *args, **options):
        id_aprendiz = options.get("id_aprendiz")

        if id_aprendiz:
            aprendices = T_apre.objects.filter(id=id_aprendiz)
            if not aprendices.exists():
                self.stdout.write(self.style.ERROR(
                    f"No se encontró el aprendiz con id={id_aprendiz}"
                ))
                return
        else:
            aprendices = T_apre.objects.all()

        for aprendiz in aprendices:
            if not aprendiz.ficha or not aprendiz.ficha.progra:
                self.stdout.write(
                    f"[{aprendiz.id}] No tiene ficha o programa asociado, se omite"
                )
                continue

            # Crear o actualizar la estructura
            crear_estructura_arbol_aprendiz(
                aprendiz, estructura_documental_aprendiz)

            self.stdout.write(self.style.SUCCESS(
                f"[{aprendiz.id}] Portafolio creado/actualizado correctamente"
            ))
