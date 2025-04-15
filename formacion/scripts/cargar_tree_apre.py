from commons.models import T_DocumentFolderAprendiz, T_apre

def crear_datos_prueba_aprendiz(aprendiz_id):
    aprendiz = T_apre.objects.get(id=aprendiz_id)

    # Crear carpetas raíz
    root_folders = {
        "1": "ACTA PLAN DE MEJORAMIENTO",
        "2": "PLANEACION SEGUIMIENTO Y EVALUACION ETAPA PRODUCTIVA",
        "3": "GUIA DE APRENDIZAJE",
        "4": "EVIDENCIAS",
        "5": "PLAN DE TRABAJO CON SUS DESCRIPTORES",
    }

    root_folder_objs = {}

    for iden, name in root_folders.items():
        root_folder_objs[iden] = T_DocumentFolderAprendiz.objects.create(
            name=name, tipo="carpeta", aprendiz=aprendiz
        )

    # Crear enlaces de carga en algunas carpetas raíz
    link_folders = {
        "2": root_folder_objs["2"],
    }

    for iden, parent in link_folders.items():
        T_DocumentFolderAprendiz.objects.create(
            name="Cargar nuevo", tipo="link", parent=parent, aprendiz=aprendiz
        )

    # Crear subcarpetas de ACTA PLAN DE MEJORAMIENTO
    subfolders_1 = ["ANALISIS", "PLANEACION", "EJECUCION", "EVALUACION"]
    for name in subfolders_1:
        sub = T_DocumentFolderAprendiz.objects.create(
            name=name, tipo="carpeta", parent=root_folder_objs["1"], aprendiz=aprendiz
        )
        T_DocumentFolderAprendiz.objects.create(
            name="Cargar nuevo", tipo="link", parent=sub, aprendiz=aprendiz
        )

    # Crear subcarpetas de GUIA DE APRENDIZAJE
    subfolders_3 = ["ANALISIS", "PLANEACION", "EJECUCION", "EVALUACION"]
    subfolder_objs_3 = {}
    for name in subfolders_3:
        subfolder_objs_3[name] = T_DocumentFolderAprendiz.objects.create(
            name=name, tipo="carpeta", parent=root_folder_objs["3"], aprendiz=aprendiz
        )

    # Crear sub-subcarpetas en GUIA DE APRENDIZAJE
    for parent_name in subfolders_3:
        for sub_name in ["GUIAS DE LA FASE", "INSTRUMENTOS DE EVALUACION"]:
            sub = T_DocumentFolderAprendiz.objects.create(
                name=sub_name, tipo="carpeta", parent=subfolder_objs_3[parent_name], aprendiz=aprendiz
            )
            T_DocumentFolderAprendiz.objects.create(
                name="Cargar nuevo", tipo="link", parent=sub, aprendiz=aprendiz
            )

    # Crear subcarpetas en EVIDENCIAS y PLAN DE TRABAJO
    for root_id in ["4", "5"]:
        for name in ["ANALISIS", "PLANEACION", "EJECUCION", "EVALUACION"]:
            sub = T_DocumentFolderAprendiz.objects.create(
                name=name, tipo="carpeta", parent=root_folder_objs[root_id], aprendiz=aprendiz
            )
            T_DocumentFolderAprendiz.objects.create(
                name="Cargar nuevo", tipo="link", parent=sub, aprendiz=aprendiz
            )

    print("Datos de prueba creados exitosamente.")
