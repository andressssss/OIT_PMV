from commons.models import T_DocumentFolder, T_ficha

def crear_datos_prueba(ficha_id):
    ficha = T_ficha.objects.get(id=ficha_id)

    # Crear carpetas raíz
    root_folders = [
        "PLAN DE TRABAJO CON SUS DESCRIPTORES",
        "GFPI-F-135-GUIA DE APRENDIZAJE",
        "GORF-084-FORMATO ACTA",
        "GFPI-F-023-PLANEACIÓN, SEGUIMIENTO Y EVALUACIÓN ETAPA PRODUCTIVA",
        "FORMATO DE INASISTENCIAS",
        "ACTA PLAN DE MEJORAMIENTO",
        "EVIDENCIAS DE ESTRATEGIA DE NIVELACION",
        "FORMATO DE HOMOLOGACION",
    ]

    created_folders = {}  # Guardamos las carpetas para usarlas en la jerarquía

    for name in root_folders:
        folder = T_DocumentFolder.objects.create(name=name, tipo="carpeta", ficha=ficha)
        created_folders[name] = folder

    # Subcarpetas de "PLAN DE TRABAJO CON SUS DESCRIPTORES"
    sub_folders_1 = ["ANALISIS", "PLANEACION", "EJECUCION", "EVALUACION"]
    for sub in sub_folders_1:
        T_DocumentFolder.objects.create(name=sub, tipo="carpeta", parent=created_folders["PLAN DE TRABAJO CON SUS DESCRIPTORES"], ficha=ficha)

    # Subcarpetas de "GFPI-F-135-GUIA DE APRENDIZAJE"
    sub_folders_2 = ["ANALISIS", "PLANEACION", "EJECUCION", "EVALUACION"]
    for sub in sub_folders_2:
        subfolder = T_DocumentFolder.objects.create(name=sub, tipo="carpeta", parent=created_folders["GFPI-F-135-GUIA DE APRENDIZAJE"], ficha=ficha)

        # SubSubCarpetas de cada fase
        for subsub in ["GUIAS DE LA FASE", "INSTRUMENTOS DE EVALUACION"]:
            T_DocumentFolder.objects.create(name=subsub, tipo="carpeta", parent=subfolder, ficha=ficha)

    print("Datos de prueba creados exitosamente.")
