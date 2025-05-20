from commons.models import T_DocumentFolderAprendiz, T_apre

def crear_datos_prueba_aprendiz(aprendiz_id):
    aprendiz = T_apre.objects.get(id=aprendiz_id)

    # Crear carpetas raíz
    root_folders = {
        "1": "1. ACTA PLAN DE MEJORAMIENTO",
        "2": "2. PLANEACION SEGUIMIENTO Y EVALUACION ETAPA PRODUCTIVA",
        "3": "3. GUIA DE APRENDIZAJE",
        "4": "4. EVIDENCIAS",
        "5": "5. PLAN DE TRABAJO CON SUS DESCRIPTORES",
    }

    root_folder_objs = {}

    for iden, name in root_folders.items():
        root_folder_objs[iden] = T_DocumentFolderAprendiz.objects.create(
            name=name, tipo="carpeta", aprendiz=aprendiz
        )

    # Crear subcarpetas de ACTA PLAN DE MEJORAMIENTO
    subfolders_1 = ["1. ANÁLISIS", "2. PLANEACIÓN", "3. EJECUCIÓN", "4. EVALUACIÓN"]
    for name in subfolders_1:
        T_DocumentFolderAprendiz.objects.create(
            name=name, tipo="carpeta", parent=root_folder_objs["1"], aprendiz=aprendiz
        )

    # Crear subcarpetas de GUIA DE APRENDIZAJE
    subfolders_3 = ["1. ANÁLISIS", "2. PLANEACIÓN", "3. EJECUCIÓN", "4. EVALUACIÓN"]
    subfolder_objs_3 = {}
    for name in subfolders_3:
        subfolder_objs_3[name] = T_DocumentFolderAprendiz.objects.create(
            name=name, tipo="carpeta", parent=root_folder_objs["3"], aprendiz=aprendiz
        )

    # Crear sub-subcarpetas en GUIA DE APRENDIZAJE
    for parent_name in subfolders_3:
        for sub_name in ["GUIAS DE LA FASE", "INSTRUMENTOS DE EVALUACION"]:
            T_DocumentFolderAprendiz.objects.create(
                name=sub_name, tipo="carpeta", parent=subfolder_objs_3[parent_name], aprendiz=aprendiz
            )

    # Crear subcarpetas en EVIDENCIAS y PLAN DE TRABAJO
    for root_id in ["4", "5"]:
        for name in ["1. ANÁLISIS", "2. PLANEACIÓN", "3. EJECUCIÓN", "4. EVALUACIÓN"]:
            T_DocumentFolderAprendiz.objects.create(
                name=name, tipo="carpeta", parent=root_folder_objs[root_id], aprendiz=aprendiz
            )

    print("Estructura documental creada exitosamente para el aprendiz:", aprendiz_id)
