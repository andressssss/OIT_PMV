from commons.models import T_DocumentFolder, T_ficha

def crear_datos_prueba(ficha_id):
    ficha = T_ficha.objects.get(id=ficha_id)

    # Crear Carpeta Principal 1
    root_folder_1 = T_DocumentFolder.objects.create(name="PLAN DE TRABAJO CON SUS DESCRIPTORES", tipo="carpeta", ficha=ficha)
    root_folder_2 = T_DocumentFolder.objects.create(name="GFPI-F-135-GUIA DE APRENDIZAJE", tipo="carpeta", ficha=ficha)
    root_folder_3 = T_DocumentFolder.objects.create(name="GORF-084-FORMATO ACTA", tipo="carpeta", ficha=ficha, iden="3")
    link_root_folder_3 = T_DocumentFolder.objects.create(name="Cargar nuevo", tipo="link", parent=root_folder_3, ficha=ficha, url = "3/cargar_link_folders")

    root_folder_4 = T_DocumentFolder.objects.create(name="GFPI-F-023-PLANEACIÓN, SEGUIMIENTO Y EVALUACIÓN ETAPA PRODUCTIVA", tipo="carpeta", ficha=ficha, iden="4")
    link_root_folder_4 = T_DocumentFolder.objects.create(name="Cargar nuevo", tipo="link", parent=root_folder_4, ficha=ficha, url= "4/cargar_link_folders")

    root_folder_5 = T_DocumentFolder.objects.create(name="FORMATO DE INASISTENCIAS", tipo="carpeta", ficha=ficha, iden="5")
    link_root_folder_5 = T_DocumentFolder.objects.create(name="Cargar nuevo", tipo="link", parent=root_folder_5, ficha=ficha, url = "5/cargar_link_folders")

    root_folder_6 = T_DocumentFolder.objects.create(name="ACTA PLAN DE MEJORAMIENTO", tipo="carpeta", ficha=ficha)
    root_folder_7 = T_DocumentFolder.objects.create(name="EVIDENCIAS DE ESTRATEGIA DE NIVELACION", tipo="carpeta", ficha=ficha, iden="7")
    link_root_folder_7 = T_DocumentFolder.objects.create(name="Cargar nuevo", tipo="link", parent=root_folder_7, ficha=ficha, url="7/cargar_link_folders")

    root_folder_8 = T_DocumentFolder.objects.create(name="FORMATO DE HOMOLOGACION", tipo="carpeta", ficha=ficha, iden="8")
    link_root_folder_8 = T_DocumentFolder.objects.create(name="Cargar nuevo", tipo="link", parent=root_folder_8, ficha=ficha, url="8/cargar_link_folders")

    # Subcarpetas 1
    subfolder1_1 = T_DocumentFolder.objects.create(name="ANALISIS", tipo="carpeta", parent=root_folder_1, ficha=ficha, iden="1_1")
    link_subfolder1_1 = T_DocumentFolder.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder1_1, ficha=ficha, url="1_1/cargar_link_folders")
    
    subfolder2_1 = T_DocumentFolder.objects.create(name="PLANEACION", tipo="carpeta", parent=root_folder_1, ficha=ficha, iden="1_2")
    link_subfolder2_1 = T_DocumentFolder.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder2_1, ficha=ficha, url="1_2/cargar_link_folders")

    subfolder3_1 = T_DocumentFolder.objects.create(name="EJECUCION ", tipo="carpeta", parent=root_folder_1, ficha=ficha, iden="1_3")
    link_subfolder3_1 = T_DocumentFolder.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder3_1, ficha=ficha, url="1_3/cargar_link_folders")

    subfolder4_1 = T_DocumentFolder.objects.create(name="EVALUACION", tipo="carpeta", parent=root_folder_1, ficha=ficha, iden="1_4")
    link_subfolder4_1 = T_DocumentFolder.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder4_1, ficha=ficha, url="1_4/cargar_link_folders")

    # Subcarpetas 2
    subfolder1_2 = T_DocumentFolder.objects.create(name="ANALISIS", tipo="carpeta", parent=root_folder_2, ficha=ficha)
    subfolder2_2 = T_DocumentFolder.objects.create(name="PLANEACION", tipo="carpeta", parent=root_folder_2, ficha=ficha)
    subfolder3_2 = T_DocumentFolder.objects.create(name="EJECUCION ", tipo="carpeta", parent=root_folder_2, ficha=ficha)
    subfolder4_2 = T_DocumentFolder.objects.create(name="EVALUACION", tipo="carpeta", parent=root_folder_2, ficha=ficha)

    # SubSubCarpetas
    subfolder1_2_1 = T_DocumentFolder.objects.create(name="GUIAS DE LA FASE", tipo="carpeta", parent=subfolder1_2, ficha=ficha, iden="2_1_1")
    link_subfolder1_2_1 = T_DocumentFolder.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder1_2_1, ficha=ficha, url="2_1_1/cargar_link_folders")

    subfolder2_2_1 = T_DocumentFolder.objects.create(name="INSTRUMENTOS DE EVALUACION", tipo="carpeta", parent=subfolder1_2, ficha=ficha, iden="2_1_2")
    link_subfolder2_2_1 = T_DocumentFolder.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder2_2_1, ficha=ficha, url="2_1_2/cargar_link_folders")

    subfolder1_2_2 = T_DocumentFolder.objects.create(name="GUIAS DE LA FASE", tipo="carpeta", parent=subfolder2_2, ficha=ficha, iden="2_2_1")
    link_subfolder1_2_2 = T_DocumentFolder.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder1_2_2, ficha=ficha, url="2_2_1/cargar_link_folders")

    subfolder2_2_2 = T_DocumentFolder.objects.create(name="INSTRUMENTOS DE EVALUACION", tipo="carpeta", parent=subfolder2_2, ficha=ficha, iden="2_2_2")
    link_subfolder2_2_2 = T_DocumentFolder.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder2_2_2, ficha=ficha, url="2_2_2/cargar_link_folders")

    subfolder1_2_3 = T_DocumentFolder.objects.create(name="GUIAS DE LA FASE", tipo="carpeta", parent=subfolder3_2, ficha=ficha, iden="2_3_1")
    link_subfolder1_2_3 = T_DocumentFolder.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder1_2_3, ficha=ficha, url="2_3_1/cargar_link_folders")

    subfolder2_2_3 = T_DocumentFolder.objects.create(name="INSTRUMENTOS DE EVALUACION", tipo="carpeta", parent=subfolder3_2, ficha=ficha, iden="2_3_2")
    link_subfolder2_2_3 = T_DocumentFolder.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder2_2_3, ficha=ficha, url="2_3_2/cargar_link_folders")

    subfolder1_2_4 = T_DocumentFolder.objects.create(name="GUIAS DE LA FASE", tipo="carpeta", parent=subfolder4_2, ficha=ficha, iden="2_4_1")
    link_subfolder1_2_4 = T_DocumentFolder.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder1_2_4, ficha=ficha, url="2_4_1/cargar_link_folders")

    subfolder2_2_4 = T_DocumentFolder.objects.create(name="INSTRUMENTOS DE EVALUACION", tipo="carpeta", parent=subfolder4_2, ficha=ficha, iden="2_4_2")
    link_subfolder2_2_5 = T_DocumentFolder.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder2_2_4, ficha=ficha, url="2_4_2/cargar_link_folders")

    # Subcarpetas 6
    subfolder1_6 = T_DocumentFolder.objects.create(name="ANALISIS", tipo="carpeta", parent=root_folder_6, ficha=ficha, iden="6_1")
    link_subfolder1_6 = T_DocumentFolder.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder1_6, ficha=ficha, url="6_1/cargar_link_folders")

    subfolder2_6 = T_DocumentFolder.objects.create(name="PLANEACION", tipo="carpeta", parent=root_folder_6, ficha=ficha, iden="6_2")
    link_subfolder2_6 = T_DocumentFolder.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder2_6, ficha=ficha, url="6_2/cargar_link_folders")

    subfolder3_6 = T_DocumentFolder.objects.create(name="EJECUCION ", tipo="carpeta", parent=root_folder_6, ficha=ficha, iden="6_3")
    link_subfolder3_6 = T_DocumentFolder.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder3_6, ficha=ficha, url="6_3/cargar_link_folders")

    subfolder4_6 = T_DocumentFolder.objects.create(name="EVALUACION", tipo="carpeta", parent=root_folder_6, ficha=ficha, iden="6_4")
    link_subfolder4_6 = T_DocumentFolder.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder4_6, ficha=ficha, url="6_4/cargar_link_folders")

    print("Datos de prueba creados exitosamente.") 
