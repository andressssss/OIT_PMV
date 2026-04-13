import json
from django.db import transaction
from commons.models import (
    T_PlantillaNodo, T_PlantillaVersion, T_PlantillaAplicacion,
    T_DocumentFolder, T_ficha
)


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
            "children": [serializar_nodo(h) for h in nodo.get_children().order_by("orden")],
        }
    raices = T_PlantillaNodo.objects.filter(parent=None).order_by("orden")
    return [serializar_nodo(r) for r in raices]


def guardar_version(descripcion, auto_aplicar_nuevas, usuario):
    """Create a new version with a snapshot of current plantilla state."""
    ultima = T_PlantillaVersion.objects.order_by("-version").first()
    nueva_version = (ultima.version + 1) if ultima else 1

    if auto_aplicar_nuevas:
        T_PlantillaVersion.objects.filter(auto_aplicar_nuevas=True).update(auto_aplicar_nuevas=False)

    snapshot = generar_snapshot()
    version = T_PlantillaVersion.objects.create(
        version=nueva_version,
        snapshot=snapshot,
        descripcion=descripcion,
        auto_aplicar_nuevas=auto_aplicar_nuevas,
        usuario=usuario,
    )
    return version


def restaurar_version(version_id, usuario):
    """Restore plantilla tree from a previous version's snapshot."""
    version_origen = T_PlantillaVersion.objects.get(id=version_id)

    with transaction.atomic():
        T_PlantillaNodo.objects.all().delete()

        def crear_desde_snapshot(nodos, parent):
            for nodo_data in nodos:
                nodo = T_PlantillaNodo.objects.create(
                    name=nodo_data["name"],
                    parent=parent,
                    orden=nodo_data["orden"],
                    activo=nodo_data["activo"],
                    roles_visibles=nodo_data.get("roles_visibles"),
                    roles_editables=nodo_data.get("roles_editables"),
                    usuario_crea=usuario,
                )
                crear_desde_snapshot(nodo_data.get("children", []), nodo)

        crear_desde_snapshot(version_origen.snapshot, None)
        T_PlantillaNodo.objects.rebuild()

    return guardar_version(
        f"Restaurada desde v{version_origen.version}",
        version_origen.auto_aplicar_nuevas,
        usuario,
    )


def preview_aplicar(version_id, fichas_qs):
    """Preview what changes would be applied to a set of fichas."""
    version = T_PlantillaVersion.objects.get(id=version_id)
    plantilla_nodos = T_PlantillaNodo.objects.filter(parent=None).order_by("orden")

    resumen = {
        "total_fichas": fichas_qs.count(),
        "fichas_preview": [],
    }

    for ficha in fichas_qs[:10]:
        cambios = _calcular_cambios(ficha, plantilla_nodos)
        resumen["fichas_preview"].append({
            "ficha_num": ficha.num,
            "ficha_id": ficha.id,
            "nodos_a_crear": cambios["crear"],
            "nodos_a_ocultar": cambios["ocultar"],
            "nodos_a_sincronizar": cambios["sincronizar"],
        })

    return resumen


@transaction.atomic
def ejecutar_aplicar(version_id, fichas_qs, usuario):
    """Apply a plantilla version to a set of fichas."""
    version = T_PlantillaVersion.objects.get(id=version_id)
    plantilla_nodos = T_PlantillaNodo.objects.filter(parent=None).order_by("orden")

    resultados = []
    for ficha in fichas_qs:
        try:
            detalle = _aplicar_a_ficha(ficha, plantilla_nodos)
            resultado = "exitoso"
        except Exception as e:
            detalle = {"error": str(e)}
            resultado = "error"

        T_PlantillaAplicacion.objects.create(
            version=version,
            ficha=ficha,
            resultado=resultado,
            detalle=detalle,
            usuario=usuario,
        )
        resultados.append({
            "ficha_num": ficha.num,
            "ficha_id": ficha.id,
            "resultado": resultado,
            "detalle": detalle,
        })

    return resultados


def aplicar_a_ficha_nueva(ficha):
    """Apply auto-apply version to a newly created ficha. Called from ficha creation flows."""
    version = T_PlantillaVersion.objects.filter(auto_aplicar_nuevas=True).first()
    if not version:
        return None
    plantilla_nodos = T_PlantillaNodo.objects.filter(parent=None).order_by("orden")
    return _aplicar_a_ficha(ficha, plantilla_nodos)


def obtener_fichas_por_seleccion(modo, valor=None):
    """Return a queryset of fichas based on selection mode."""
    if modo == "todas":
        return T_ficha.objects.all()
    elif modo == "corte":
        return T_ficha.objects.filter(corte=valor)
    elif modo == "listado":
        nums = [n.strip() for n in valor.replace(",", "\n").split("\n") if n.strip()]
        return T_ficha.objects.filter(num__in=nums)
    return T_ficha.objects.none()


# --- Private helpers ---

def _calcular_cambios(ficha, plantilla_raices):
    """Calculate what changes are needed for a ficha against the plantilla."""
    cambios = {"crear": [], "ocultar": [], "sincronizar": []}

    def recorrer(plantilla_nodos, parent_folder_id):
        for nodo in plantilla_nodos:
            existente = T_DocumentFolder.objects.filter(
                ficha=ficha, name=nodo.name, parent_id=parent_folder_id
            ).first()

            if not existente and nodo.activo:
                cambios["crear"].append(nodo.name)
            elif existente and not nodo.activo:
                if not existente.oculto:
                    cambios["ocultar"].append(nodo.name)
            elif existente and nodo.activo:
                if (existente.roles_visibles != nodo.roles_visibles or
                        existente.roles_editables != nodo.roles_editables):
                    cambios["sincronizar"].append(nodo.name)

            if existente:
                hijos = nodo.get_children().order_by("orden")
                if hijos.exists():
                    recorrer(hijos, existente.id)
            elif nodo.activo:
                hijos = nodo.get_children().order_by("orden")
                if hijos.exists():
                    cambios["crear"].extend([h.name for h in hijos if h.activo])

    recorrer(plantilla_raices, None)
    return cambios


def _aplicar_a_ficha(ficha, plantilla_raices):
    """Apply the plantilla to a single ficha. Returns detail dict."""
    detalle = {"creados": [], "ocultados": [], "sincronizados": []}

    def recorrer(plantilla_nodos, parent_folder):
        for nodo in plantilla_nodos:
            existente = T_DocumentFolder.objects.filter(
                ficha=ficha, name=nodo.name, parent=parent_folder
            ).first()

            if not existente and nodo.activo:
                existente = T_DocumentFolder.objects.create(
                    name=nodo.name,
                    tipo="carpeta",
                    ficha=ficha,
                    parent=parent_folder,
                    oculto=False,
                    roles_visibles=nodo.roles_visibles,
                    roles_editables=nodo.roles_editables,
                )
                detalle["creados"].append(nodo.name)
            elif existente and not nodo.activo:
                if not existente.oculto:
                    existente.oculto = True
                    existente.save(update_fields=["oculto"])
                    detalle["ocultados"].append(nodo.name)
            elif existente and nodo.activo:
                changed = False
                if existente.roles_visibles != nodo.roles_visibles:
                    existente.roles_visibles = nodo.roles_visibles
                    changed = True
                if existente.roles_editables != nodo.roles_editables:
                    existente.roles_editables = nodo.roles_editables
                    changed = True
                if existente.oculto:
                    existente.oculto = False
                    changed = True
                if changed:
                    existente.save(update_fields=["oculto", "roles_visibles", "roles_editables"])
                    detalle["sincronizados"].append(nodo.name)

            if existente:
                hijos = nodo.get_children().order_by("orden")
                if hijos.exists():
                    recorrer(hijos, existente)

    recorrer(plantilla_raices, None)
    return detalle
