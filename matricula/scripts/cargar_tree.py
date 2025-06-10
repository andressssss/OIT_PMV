from commons.models import T_DocumentFolder, T_ficha

def crear_datos_prueba(ficha_id):
    ficha = T_ficha.objects.get(id=ficha_id)

    # Crear carpetas raíz
    root_folders = [
        "1. PLAN DE TRABAJO CONCERTADO CON SUS DESCRIPTORES",
        "2. GFPI-F-135-GUÍA DE APRENDIZAJE",
        "3. GORF-084-FORMATO ACTA",
        "4. GFPI-F-023-PLANEACIÓN, SEGUIMIENTO Y EVALUACIÓN ETAPA PRODUCTIVA",
        "5. FORMATO DE INASISTENCIAS",
        "6. ACTA PLAN DE MEJORAMIENTO",
        "7. EVIDENCIAS DE ESTRATEGIA DE NIVELACIÓN",
        "8. FORMATO DE HOMOLOGACIÓN",
    ]

    created_folders = {}  # Guardamos las carpetas para usarlas en la jerarquía

    for name in root_folders:
        folder = T_DocumentFolder.objects.create(name=name, tipo="carpeta", ficha=ficha)
        created_folders[name] = folder

    # Subcarpetas de "PLAN DE TRABAJO CON SUS DESCRIPTORES"
    sub_folders_1 = ["1. ANÁLISIS", "2. PLANEACIÓN", "3. EJECUCIÓN", "4. EVALUACIÓN"]
    for sub in sub_folders_1:
        T_DocumentFolder.objects.create(name=sub, tipo="carpeta", parent=created_folders["1. PLAN DE TRABAJO CONCERTADO CON SUS DESCRIPTORES"], ficha=ficha)

    # Subcarpetas de "GFPI-F-135-GUIA DE APRENDIZAJE"
    sub_folders_2 = ["1. ANÁLISIS", "2. PLANEACIÓN", "3. EJECUCIÓN", "4. EVALUACIÓN"]
    for sub in sub_folders_2:
        subfolder = T_DocumentFolder.objects.create(name=sub, tipo="carpeta", parent=created_folders["2. GFPI-F-135-GUÍA DE APRENDIZAJE"], ficha=ficha)

        # SubSubCarpetas de cada fase
        for subsub in ["GUÍAS DE LA FASE", "INSTRUMENTOS DE EVALUACIÓN"]:
            T_DocumentFolder.objects.create(name=subsub, tipo="carpeta", parent=subfolder, ficha=ficha)

    # Sub carpetas FORMATO ACTA
    sub_folders_3 = ["ELECCIÓN DEL VOCERO", "COMITÉ ACADÉMICO", "CERTIFICACIÓN DE TRANSVERSALES FINALIZACIONES", "DESERCIONES Y RETIROS VOLUNTARIOS"]
    for sub in sub_folders_3:
        subfolder = T_DocumentFolder.objects.create(name=sub, tipo="carpeta", parent=created_folders["3. GORF-084-FORMATO ACTA"], ficha=ficha)

    # Subcarpetas de 6. ACTA PLAN DE MEJORAMIENTO
    sub_folders_4 = ["1. ANÁLISIS", "2. PLANEACIÓN", "3. EJECUCIÓN", "4. EVALUACIÓN"]
    for sub in sub_folders_4:
        T_DocumentFolder.objects.create(name=sub, tipo="carpeta", parent=created_folders["6. ACTA PLAN DE MEJORAMIENTO"], ficha=ficha)


    print("Datos de portafolio creados exitosamente.")
