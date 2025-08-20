from commons.models import T_DocumentFolderAprendiz, T_apre, T_fase, T_compe, T_raps

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
    """
    Crea la estructura de carpetas para un aprendiz.
    Si encuentra la clave '4. EVIDENCIAS DE APRENDIZAJE',
    genera dinámicamente las subcarpetas según fases, competencias y RAPs.
    """
    for nombre, hijos in estructura.items():
        carpeta = T_DocumentFolderAprendiz.objects.create(
            name=nombre,
            tipo="carpeta",
            aprendiz=aprendiz,
            parent=parent
        )

        if nombre == "4. EVIDENCIAS DE APRENDIZAJE":
            fases = T_fase.objects.filter(
                nom__in=FASES_LABELS.keys()
            ).order_by('id')

            for fase in fases:
                carpeta_fase = T_DocumentFolderAprendiz.objects.create(
                    name=FASES_LABELS.get(fase.nom.upper(), fase.nom),
                    tipo="carpeta",
                    aprendiz=aprendiz,
                    parent=carpeta
                )

                raps_fase = T_raps.objects.filter(
                    progra=aprendiz.ficha.progra,
                    fase=fase
                ).select_related('compe', 'progra')

                competencias = {}
                for rap in raps_fase:
                    competencias.setdefault(rap.compe, []).append(rap)

                for compe, raps in competencias.items():
                    carpeta_compe = T_DocumentFolderAprendiz.objects.create(
                        name=f"{compe.cod} - {compe.nom}",
                        tipo="carpeta",
                        aprendiz=aprendiz,
                        parent=carpeta_fase
                    )
                    for rap in raps:
                        T_DocumentFolderAprendiz.objects.create(
                            name=rap.nom,
                            tipo="carpeta",
                            aprendiz=aprendiz,
                            parent=carpeta_compe
                        )

        elif hijos:
            crear_estructura_arbol_aprendiz(aprendiz, hijos, carpeta)


def crear_datos_prueba_aprendiz(aprendiz_id):
    aprendiz = T_apre.objects.get(id=aprendiz_id)
    crear_estructura_arbol_aprendiz(aprendiz, estructura_documental_aprendiz)
    print(
        f"Estructura documental creada exitosamente para el aprendiz {aprendiz_id}")
