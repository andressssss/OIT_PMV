from django.core.management.base import BaseCommand
from commons.models import T_DocumentFolder, T_ficha

estructura_documental = {
    "1. PLAN DE TRABAJO CONCERTADO CON SUS DESCRIPTORES": {
        "1. ANÁLISIS": {},
        "2. PLANEACIÓN": {},
        "3. EJECUCIÓN": {},
        "4. EVALUACIÓN": {},
    },
    "2. GFPI-F-135-GUÍA DE APRENDIZAJE": {
        "1. ANÁLISIS": {
            "GUÍAS DE LA FASE": {},
            "INSTRUMENTOS DE EVALUACIÓN": {},
        },
        "2. PLANEACIÓN": {
            "GUÍAS DE LA FASE": {},
            "INSTRUMENTOS DE EVALUACIÓN": {},
        },
        "3. EJECUCIÓN": {
            "GUÍAS DE LA FASE": {},
            "INSTRUMENTOS DE EVALUACIÓN": {},
        },
        "4. EVALUACIÓN": {
            "GUÍAS DE LA FASE": {},
            "INSTRUMENTOS DE EVALUACIÓN": {},
        },
    },
    "3. GORF-084-FORMATO ACTA": {
        "ELECCIÓN REPRESENTANTE VOCERO": {},
        "ELEVACIÓN Y SEGUIMIENTO A COMITÉ ACADÉMICO": {},
        "CERTIFICACIÓN DE TRANSVERSALES FINALIZACIONES": {},
        "ENTREGA Y SOCIALIZACIÓN DE LA INDUCCIÓN APRENDICES": {},
        "SENSIBILIZACIÓN DE LA ETAPA PRODUCTIVA": {},
        "SOCIALIZACIÓN DE ESTRUCTURA CURRICULAR": {},
    },
    "4. GFPI-F-023-PLANEACIÓN, SEGUIMIENTO Y EVALUACIÓN ETAPA PRODUCTIVA": {
        "GFPI-F-023-PLANEACIÓN, SEGUIMIENTO Y EVALUACIÓN ETAPA PRODUCTIVA": {},
        "GFPI-F-147-BITACORAS SEGUIMIENTO ETAPA PRODUCTIVA": {},
        "GFPI-F-165-V3-INSCRIPCIÓN A ETAPA PRODUCTIVA": {},
        "PROCESO DE CERTIFICACIÓN": {},
    },
    "5. FORMATO DE INASISTENCIAS": {},
    "6. ACTA PLAN DE MEJORAMIENTO": {
        "1. ANÁLISIS": {},
        "2. PLANEACIÓN": {},
        "3. EJECUCIÓN": {},
        "4. EVALUACIÓN": {},
    },
    "7. EVIDENCIAS DE ESTRATEGIA DE INTENSIFICACIÓN": {},
    "8. FORMATO DE HOMOLOGACIÓN": {},
    "LINK DE PORTAFOLIO APRENDICES 2024": {},
}

# Renombramientos por estructura antigua → nueva
RENOMBRAR_CARPETAS = {
    "ELECCIÓN DEL VOCERO": "ELECCIÓN REPRESENTANTE VOCERO",
    "COMITÉ ACADÉMICO": "ELEVACIÓN Y SEGUIMIENTO A COMITÉ ACADÉMICO",
    "7. EVIDENCIAS DE ESTRATEGIA DE NIVELACIÓN": "7. EVIDENCIAS DE ESTRATEGIA DE INTENSIFICACIÓN",
}

CARPETAS_A_ELIMINAR = [
    "DESERCIONES Y RETIROS VOLUNTARIOS",
    "FORMATO PROGRAMACIÓN EVENTOS",
    "REPORTES JUICIOS EVALUATIVOS"
]

def get_or_create_folder(ficha, name, parent):
    # Buscar si existe una carpeta con un nombre antiguo que deba renombrarse
    for old_name, new_name in RENOMBRAR_CARPETAS.items():
        if name == new_name:
            folder_qs = T_DocumentFolder.objects.filter(name=old_name, ficha=ficha, parent=parent)
            if folder_qs.exists():
                folder = folder_qs.first()
                print(f"✏️ Renombrando carpeta '{old_name}' → '{new_name}' en ficha {ficha.num}")
                folder.name = new_name
                folder.save()
                return folder

    # Buscar si ya existe una carpeta con el nombre esperado
    folder, _ = T_DocumentFolder.objects.get_or_create(
        name=name,
        ficha=ficha,
        parent=parent,
        defaults={'tipo': 'carpeta'}
    )
    return folder


def actualizar_estructura_arbol(ficha, estructura, parent=None):
    for nombre, hijos in estructura.items():
        folder = get_or_create_folder(ficha, nombre, parent)
        actualizar_estructura_arbol(ficha, hijos, folder)

def eliminar_carpetas_obsoletas(ficha):
    for name in CARPETAS_A_ELIMINAR:
        qs = T_DocumentFolder.objects.filter(name=name, ficha=ficha)
        for folder in qs:
            print(f"🗑️ Eliminando carpeta obsoleta: {folder.name} en ficha {ficha.num}")
            folder.delete()

def renombrar_carpetas(ficha):
    for old_name, new_name in RENOMBRAR_CARPETAS.items():
        qs = T_DocumentFolder.objects.filter(name=old_name, ficha=ficha)
        for folder in qs:
            print(f"✏️ Renombrando carpeta '{old_name}' → '{new_name}' en ficha {ficha.num}")
            folder.name = new_name
            folder.save()

class Command(BaseCommand):
    help = 'Actualiza la estructura documental de todas las fichas con la nueva estructura.'

    def add_arguments(self, parser):
        parser.add_argument('--ficha', type=int, help='Número de ficha específica a actualizar')

    def handle(self, *args, **kwargs):
        ficha_num = kwargs.get('ficha')
        if ficha_num:
            fichas = T_ficha.objects.filter(num=ficha_num)
            if not fichas.exists():
                self.stdout.write(self.style.ERROR(f'❌ No existe una ficha con número {ficha_num}'))
                return
        else:
            fichas = T_ficha.objects.all()

        for ficha in fichas:
            self.stdout.write(f'\n📁 Procesando ficha {ficha.num}...')
            actualizar_estructura_arbol(ficha, estructura_documental)
            eliminar_carpetas_obsoletas(ficha)
            self.stdout.write(self.style.SUCCESS(f'✅ Ficha {ficha.num} actualizada correctamente.'))
