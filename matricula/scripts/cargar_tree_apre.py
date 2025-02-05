from commons.models import T_DocumentFolderAprendiz, T_ficha, T_apre

def crear_datos_prueba_aprendiz(ficha_id, aprendiz_id):
    ficha = T_ficha.objects.get(id=ficha_id)
    aprendiz = T_apre.objects.get(id=aprendiz_id)

    # Crear Carpeta Principal 1
    root_folder_1 = T_DocumentFolderAprendiz.objects.create(name="ACTA PLAN DE MEJORAMIENTO", tipo="carpeta", ficha=ficha, aprendiz=aprendiz, iden="1")
    root_folder_2 = T_DocumentFolderAprendiz.objects.create(name="PLANEACION SEGUIMIENTO Y EVALUACION ETAPA PRODUCTIVA", tipo="carpeta", ficha=ficha, aprendiz=aprendiz, iden="2")
    link_root_folder_2 = T_DocumentFolderAprendiz.objects.create(name="Cargar nuevo", tipo="link", parent=root_folder_2, ficha=ficha, aprendiz=aprendiz, url= "2/cargar_link_folders")
    
    root_folder_3 = T_DocumentFolderAprendiz.objects.create(name="GUIA DE APENDIZAJE", tipo="carpeta", ficha=ficha, aprendiz=aprendiz ,iden="3")

    root_folder_4 = T_DocumentFolderAprendiz.objects.create(name="EVIDENCIAS", tipo="carpeta", ficha=ficha, aprendiz=aprendiz, iden="4")

    root_folder_5 = T_DocumentFolderAprendiz.objects.create(name="PLAN DE TRABAJO CON SUS DESCRIPTORES", tipo="carpeta", ficha=ficha, aprendiz=aprendiz, iden="5")

    # Subcarpetas 1
    subfolder1_1 = T_DocumentFolderAprendiz.objects.create(name="ANALISIS", tipo="carpeta", parent=root_folder_1, ficha=ficha, aprendiz=aprendiz , iden="1_1")
    link_subfolder1_1 = T_DocumentFolderAprendiz.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder1_1, ficha=ficha, aprendiz=aprendiz , url="1_1/cargar_link_folders")
    
    subfolder2_1 = T_DocumentFolderAprendiz.objects.create(name="PLANEACION", tipo="carpeta", parent=root_folder_1, ficha=ficha, aprendiz=aprendiz, iden="1_2")
    link_subfolder2_1 = T_DocumentFolderAprendiz.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder2_1, ficha=ficha, aprendiz=aprendiz, url="1_2/cargar_link_folders")

    subfolder3_1 = T_DocumentFolderAprendiz.objects.create(name="EJECUCION ", tipo="carpeta", parent=root_folder_1, ficha=ficha, aprendiz=aprendiz, iden="1_3")
    link_subfolder3_1 = T_DocumentFolderAprendiz.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder3_1, ficha=ficha, aprendiz=aprendiz, url="1_3/cargar_link_folders")

    subfolder4_1 = T_DocumentFolderAprendiz.objects.create(name="EVALUACION", tipo="carpeta", parent=root_folder_1, ficha=ficha, aprendiz=aprendiz, iden="1_4")
    link_subfolder4_1 = T_DocumentFolderAprendiz.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder4_1, ficha=ficha, aprendiz=aprendiz, url="1_4/cargar_link_folders")

    # Subcarpetas 2
    subfolder1_3 = T_DocumentFolderAprendiz.objects.create(name="ANALISIS", tipo="carpeta", parent=root_folder_3, ficha=ficha, aprendiz=aprendiz)
    subfolder2_3 = T_DocumentFolderAprendiz.objects.create(name="PLANEACION", tipo="carpeta", parent=root_folder_3, ficha=ficha, aprendiz=aprendiz)
    subfolder3_3 = T_DocumentFolderAprendiz.objects.create(name="EJECUCION ", tipo="carpeta", parent=root_folder_3, ficha=ficha, aprendiz=aprendiz)
    subfolder4_3 = T_DocumentFolderAprendiz.objects.create(name="EVALUACION", tipo="carpeta", parent=root_folder_3, ficha=ficha, aprendiz=aprendiz)

    # SubSubCarpetas
    subfolder1_3_1 = T_DocumentFolderAprendiz.objects.create(name="GUIAS DE LA FASE", tipo="carpeta", parent=subfolder1_3, ficha=ficha, aprendiz=aprendiz, iden="3_1_1")
    link_subfolder1_3_1 = T_DocumentFolderAprendiz.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder1_3_1, ficha=ficha, aprendiz=aprendiz, url="3_1_1/cargar_link_folders")

    subfolder2_3_1 = T_DocumentFolderAprendiz.objects.create(name="INSTRUMENTOS DE EVALUACION", tipo="carpeta", parent=subfolder1_3, ficha=ficha, aprendiz=aprendiz, iden="3_1_2")
    link_subfolder2_3_1 = T_DocumentFolderAprendiz.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder2_3_1, ficha=ficha, aprendiz=aprendiz, url="3_1_2/cargar_link_folders")

    subfolder1_3_2 = T_DocumentFolderAprendiz.objects.create(name="GUIAS DE LA FASE", tipo="carpeta", parent=subfolder2_3, ficha=ficha, aprendiz=aprendiz, iden="3_2_1")
    link_subfolder1_3_2 = T_DocumentFolderAprendiz.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder1_3_2, ficha=ficha, aprendiz=aprendiz, url="3_2_1/cargar_link_folders")

    subfolder2_3_2 = T_DocumentFolderAprendiz.objects.create(name="INSTRUMENTOS DE EVALUACION", tipo="carpeta", parent=subfolder2_3, ficha=ficha, aprendiz=aprendiz, iden="3_2_2")
    link_subfolder2_3_2 = T_DocumentFolderAprendiz.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder2_3_2, ficha=ficha, aprendiz=aprendiz, url="3_2_2/cargar_link_folders")

    subfolder1_3_3 = T_DocumentFolderAprendiz.objects.create(name="GUIAS DE LA FASE", tipo="carpeta", parent=subfolder3_3, ficha=ficha, aprendiz=aprendiz , iden="3_3_1")
    link_subfolder1_3_3 = T_DocumentFolderAprendiz.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder1_3_3, ficha=ficha, aprendiz=aprendiz , url="3_3_1/cargar_link_folders")

    subfolder2_3_3 = T_DocumentFolderAprendiz.objects.create(name="INSTRUMENTOS DE EVALUACION", tipo="carpeta", parent=subfolder3_3, ficha=ficha, aprendiz=aprendiz , iden="3_3_2")
    link_subfolder2_3_3 = T_DocumentFolderAprendiz.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder2_3_3, ficha=ficha, aprendiz=aprendiz, url="3_3_2/cargar_link_folders")

    subfolder1_3_4 = T_DocumentFolderAprendiz.objects.create(name="GUIAS DE LA FASE", tipo="carpeta", parent=subfolder4_3, ficha=ficha, aprendiz=aprendiz, iden="3_4_1")
    link_subfolder1_3_4 = T_DocumentFolderAprendiz.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder1_3_4, ficha=ficha, aprendiz=aprendiz, url="3_4_1/cargar_link_folders")

    subfolder2_3_4 = T_DocumentFolderAprendiz.objects.create(name="INSTRUMENTOS DE EVALUACION", tipo="carpeta", parent=subfolder4_3, ficha=ficha, aprendiz=aprendiz, iden="3_4_2")
    link_subfolder2_3_4 = T_DocumentFolderAprendiz.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder2_3_4, ficha=ficha, aprendiz=aprendiz, url="3_4_2/cargar_link_folders")

    # Subcarpetas 4
    subfolder1_4 = T_DocumentFolderAprendiz.objects.create(name="ANALISIS", tipo="carpeta", parent=root_folder_4, ficha=ficha, aprendiz=aprendiz, iden="4_1")
    link_subfolder1_4 = T_DocumentFolderAprendiz.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder1_4, ficha=ficha, aprendiz=aprendiz, url="4_1/cargar_link_folders")

    subfolder2_4 = T_DocumentFolderAprendiz.objects.create(name="PLANEACION", tipo="carpeta", parent=root_folder_4, ficha=ficha, aprendiz=aprendiz, iden="4_2")
    link_subfolder2_4 = T_DocumentFolderAprendiz.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder2_4, ficha=ficha, aprendiz=aprendiz, url="4_2/cargar_link_folders")

    subfolder3_4 = T_DocumentFolderAprendiz.objects.create(name="EJECUCION ", tipo="carpeta", parent=root_folder_4, ficha=ficha, aprendiz=aprendiz, iden="4_3")
    link_subfolder3_4 = T_DocumentFolderAprendiz.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder3_4, ficha=ficha, aprendiz=aprendiz, url="4_3/cargar_link_folders")

    subfolder4_4 = T_DocumentFolderAprendiz.objects.create(name="EVALUACION", tipo="carpeta", parent=root_folder_4, ficha=ficha, aprendiz=aprendiz, iden="4_4")
    link_subfolder4_4 = T_DocumentFolderAprendiz.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder4_4, ficha=ficha, aprendiz=aprendiz, url="4_4/cargar_link_folders")

    # Subcarpetas 5
    subfolder1_5 = T_DocumentFolderAprendiz.objects.create(name="ANALISIS", tipo="carpeta", parent=root_folder_5, ficha=ficha, aprendiz=aprendiz, iden="5_1")
    link_subfolder1_5 = T_DocumentFolderAprendiz.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder1_5, ficha=ficha, aprendiz=aprendiz, url="5_1/cargar_link_folders")

    subfolder2_5 = T_DocumentFolderAprendiz.objects.create(name="PLANEACION", tipo="carpeta", parent=root_folder_5, ficha=ficha, aprendiz=aprendiz, iden="5_2")
    link_subfolder2_5 = T_DocumentFolderAprendiz.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder2_5, ficha=ficha, aprendiz=aprendiz, url="5_2/cargar_link_folders")

    subfolder3_5 = T_DocumentFolderAprendiz.objects.create(name="EJECUCION ", tipo="carpeta", parent=root_folder_5, ficha=ficha, aprendiz=aprendiz, iden="5_3")
    link_subfolder3_5 = T_DocumentFolderAprendiz.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder3_5, ficha=ficha, aprendiz=aprendiz, url="5_3/cargar_link_folders")

    subfolder4_5 = T_DocumentFolderAprendiz.objects.create(name="EVALUACION", tipo="carpeta", parent=root_folder_5, ficha=ficha, aprendiz=aprendiz, iden="5_4")
    link_subfolder4_5 = T_DocumentFolderAprendiz.objects.create(name="Cargar nuevo", tipo="link", parent=subfolder4_5, ficha=ficha, aprendiz=aprendiz, url="5_4/cargar_link_folders")


    print("Datos de prueba creados exitosamente.") 
