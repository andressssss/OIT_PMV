from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from commons.models import T_PlantillaNodo, T_PlantillaVersion
import json

ESTRUCTURA_INICIAL = {
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


def crear_nodos(estructura, parent, orden_base, user):
    """Recursively create T_PlantillaNodo from dict structure."""
    for i, (nombre, hijos) in enumerate(estructura.items()):
        nodo = T_PlantillaNodo.objects.create(
            name=nombre,
            parent=parent,
            orden=orden_base + i,
            activo=True,
            usuario_crea=user,
        )
        if hijos:
            crear_nodos(hijos, nodo, 0, user)


def generar_snapshot():
    """Generate a JSON snapshot of the current T_PlantillaNodo tree."""
    def serializar_nodo(nodo):
        return {
            "id": nodo.id,
            "name": nodo.name,
            "orden": nodo.orden,
            "activo": nodo.activo,
            "roles_visibles": nodo.roles_visibles,
            "roles_editables": nodo.roles_editables,
            "children": [serializar_nodo(h) for h in nodo.get_children()],
        }
    raices = T_PlantillaNodo.objects.filter(parent=None).order_by("orden")
    return [serializar_nodo(r) for r in raices]


class Command(BaseCommand):
    help = "Carga la estructura documental actual como plantilla v1"

    def handle(self, *args, **options):
        if T_PlantillaNodo.objects.exists():
            self.stdout.write(self.style.WARNING(
                "Ya existen nodos en la plantilla. Abortando."
            ))
            return

        user = User.objects.filter(is_superuser=True).first()
        if not user:
            self.stdout.write(self.style.ERROR("No hay superusuario. Crea uno primero."))
            return

        crear_nodos(ESTRUCTURA_INICIAL, None, 0, user)
        T_PlantillaNodo.objects.rebuild()

        snapshot = generar_snapshot()
        T_PlantillaVersion.objects.create(
            version=1,
            snapshot=snapshot,
            descripcion="Estructura inicial migrada desde codigo",
            auto_aplicar_nuevas=True,
            usuario=user,
        )

        total = T_PlantillaNodo.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f"Plantilla v1 creada: {total} nodos cargados"
        ))
