from django.core.management.base import BaseCommand
from commons.models import T_apre, T_DocumentFolderAprendiz, T_fase, T_raps
import unicodedata

FASES_LABELS = {
    "ANALISIS": "1. ANÁLISIS",
    "PLANEACION": "2. PLANEACIÓN",
    "EJECUCION": "3. EJECUCIÓN",
    "EVALUACION": "4. EVALUACIÓN"
}


def normalizar(texto):
    """Convierte a mayúsculas y elimina acentos."""
    if not texto:
        return ""
    texto = texto.upper()
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )


def extraer_nombre_fase(carpeta_name):
    """
    Convierte '1. ANÁLISIS' -> 'analisis'
    """
    # Normaliza y elimina acentos
    texto = normalizar(carpeta_name)
    # Quita el número inicial y el punto
    partes = texto.split('. ', 1)
    if len(partes) > 1:
        texto = partes[1]
    return texto.lower()  # Coincidirá con T_fase.nom en la BD

class Command(BaseCommand):
    help = "Actualiza la carpeta 4. EVIDENCIAS DE APRENDIZAJE"

    def add_arguments(self, parser):
        parser.add_argument(
            '--id_aprendiz',
            type=int,
            help='ID de un aprendiz específico para actualizar su portafolio'
        )

    def handle(self, *args, **options):
        id_aprendiz = options.get('id_aprendiz')

        if id_aprendiz:
            aprendices = T_apre.objects.filter(id=id_aprendiz)
            if not aprendices.exists():
                self.stdout.write(self.style.ERROR(
                    f"No se encontró el aprendiz con id={id_aprendiz}"))
                return
        else:
            aprendices = T_apre.objects.all()

        for aprendiz in aprendices:
            # Validar si el aprendiz tiene ficha y programa
            if not aprendiz.ficha or not aprendiz.ficha.progra:
                self.stdout.write(
                    f"[{aprendiz.id}] No tiene ficha o programa asociado, se omite"
                )
                continue

            carpeta_4 = T_DocumentFolderAprendiz.objects.filter(
                aprendiz=aprendiz,
                name="4. EVIDENCIAS DE APRENDIZAJE"
            ).first()

            if not carpeta_4:
                self.stdout.write(
                    f"[{aprendiz.id}] No tiene carpeta 4. EVIDENCIAS DE APRENDIZAJE")
                continue

            fases_carpeta = T_DocumentFolderAprendiz.objects.filter(
                parent=carpeta_4
            )

            for fase_carpeta in fases_carpeta:
                nombre_fase_bd = extraer_nombre_fase(fase_carpeta.name)
                fase_obj = T_fase.objects.filter(nom=nombre_fase_bd).first()

                if not fase_obj:
                    self.stdout.write(
                        f"[{aprendiz.id}] No se encontró T_fase para '{fase_carpeta.name}' -> '{nombre_fase_bd}'")
                    continue
                  
                if nombre_fase_bd == "analisis":
                    if not T_DocumentFolderAprendiz.objects.filter(
                        parent=fase_carpeta,
                        name="COMPETENCIA DE LA INDUCCIÓN"
                    ).exists():
                        T_DocumentFolderAprendiz.objects.create(
                            name="COMPETENCIA DE LA INDUCCIÓN",
                            tipo="carpeta",
                            aprendiz=aprendiz,
                            parent=fase_carpeta
                        )
                        self.stdout.write(f"[{aprendiz.id}] 📂 Carpeta 'COMPETENCIA DE LA INDUCCIÓN' creada en {fase_carpeta.name}")


                raps_fase = T_raps.objects.filter(
                    progra=aprendiz.ficha.progra,
                    fase=fase_obj
                ).select_related('compe', 'progra')

                competencias = {}
                for rap in raps_fase:
                    competencias.setdefault(rap.compe, []).append(rap)

                for compe, raps in competencias.items():
                    nombre_competencia = f"COMPETENCIA {compe.cod} - {compe.nom}"
                    if T_DocumentFolderAprendiz.objects.filter(
                        parent=fase_carpeta,
                        name=nombre_competencia
                    ).exists():
                        continue

                    carpeta_compe = T_DocumentFolderAprendiz.objects.create(
                        name=nombre_competencia,
                        tipo="carpeta",
                        aprendiz=aprendiz,
                        parent=fase_carpeta
                    )

                    for rap in raps:
                        T_DocumentFolderAprendiz.objects.create(
                            name=rap.nom,
                            tipo="carpeta",
                            aprendiz=aprendiz,
                            parent=carpeta_compe
                        )

            self.stdout.write(self.style.SUCCESS(
                f"[{aprendiz.id}] Actualización completada"))
