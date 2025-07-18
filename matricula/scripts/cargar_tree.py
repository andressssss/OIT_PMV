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
    "FORMATO PROGRAMACIÓN EVENTOS": {},
    "REPORTES JUICIOS EVALUATIVOS": {
        "1. CRONOGRAMA DE JUICIOS EVALUATIVOS": {},
        "2. REPORTE DE JUICIOS EVALUATIVOS": {},
    },
}

def crear_estructura_arbol(ficha, estructura, parent=None):
    for nombre, hijos in estructura.items():
        folder = T_DocumentFolder.objects.create(name=nombre, tipo="carpeta", ficha=ficha, parent=parent)
        crear_estructura_arbol(ficha, hijos, folder)

def crear_datos_prueba(ficha_id):
    ficha = T_ficha.objects.get(id=ficha_id)
    crear_estructura_arbol(ficha, estructura_documental)
    print("Datos de portafolio creados exitosamente.")
