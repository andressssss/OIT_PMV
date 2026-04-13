import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from commons.models import (
    T_PlantillaNodo, T_PlantillaVersion, T_PlantillaAplicacion, T_ficha
)
from plantillas.decorators import plantilla_admin_required
from plantillas.services import (
    generar_snapshot, guardar_version, restaurar_version,
    preview_aplicar, ejecutar_aplicar, obtener_fichas_por_seleccion,
)


# --- Page views ---

@plantilla_admin_required
def editor(request):
    return render(request, 'plantillas/editor.html')


@plantilla_admin_required
def historial(request):
    return render(request, 'plantillas/historial.html')


@plantilla_admin_required
def aplicar(request):
    return render(request, 'plantillas/aplicar.html')


@plantilla_admin_required
def log_aplicaciones(request):
    return render(request, 'plantillas/log.html')


# --- Tree API ---

@plantilla_admin_required
@require_GET
def api_obtener_nodos(request):
    """Return the full plantilla tree as nested JSON for Wunderbaum."""
    def serializar(nodo):
        children = [serializar(h) for h in nodo.get_children().order_by("orden")]
        data = {
            "title": nodo.name,
            "key": str(nodo.id),
            "data": {
                "id": nodo.id,
                "orden": nodo.orden,
                "activo": nodo.activo,
                "roles_visibles": nodo.roles_visibles,
                "roles_editables": nodo.roles_editables,
            },
            "expanded": True,
            "children": children,
        }
        if not nodo.activo:
            data["extraClasses"] = "nodo-inactivo"
        return data

    raices = T_PlantillaNodo.objects.filter(parent=None).order_by("orden")
    tree = [serializar(r) for r in raices]
    return JsonResponse(tree, safe=False)


@plantilla_admin_required
@require_POST
def api_crear_nodo(request):
    body = json.loads(request.body)
    parent_id = body.get("parent_id")
    name = body.get("name", "Nueva carpeta")

    parent = T_PlantillaNodo.objects.get(id=parent_id) if parent_id else None
    hermanos = T_PlantillaNodo.objects.filter(parent=parent)
    max_orden = max((h.orden for h in hermanos), default=-1) + 1

    nodo = T_PlantillaNodo.objects.create(
        name=name,
        parent=parent,
        orden=max_orden,
        usuario_crea=request.user,
    )
    T_PlantillaNodo.objects.rebuild()
    return JsonResponse({"id": nodo.id, "name": nodo.name, "orden": nodo.orden})


@plantilla_admin_required
@require_POST
def api_editar_nodo(request, nodo_id):
    body = json.loads(request.body)
    nodo = T_PlantillaNodo.objects.get(id=nodo_id)
    nodo.name = body.get("name", nodo.name)
    nodo.save(update_fields=["name"])
    return JsonResponse({"id": nodo.id, "name": nodo.name})


@plantilla_admin_required
@require_POST
def api_mover_nodo(request, nodo_id):
    body = json.loads(request.body)
    nodo = T_PlantillaNodo.objects.get(id=nodo_id)
    new_parent_id = body.get("parent_id")
    new_orden = body.get("orden", 0)

    new_parent = T_PlantillaNodo.objects.get(id=new_parent_id) if new_parent_id else None
    nodo.parent = new_parent
    nodo.orden = new_orden
    nodo.save(update_fields=["parent", "orden"])
    T_PlantillaNodo.objects.rebuild()
    return JsonResponse({"ok": True})


@plantilla_admin_required
@require_POST
def api_toggle_nodo(request, nodo_id):
    nodo = T_PlantillaNodo.objects.get(id=nodo_id)
    nodo.activo = not nodo.activo
    nodo.save(update_fields=["activo"])
    return JsonResponse({"id": nodo.id, "activo": nodo.activo})


@plantilla_admin_required
@require_POST
def api_visibilidad_nodo(request, nodo_id):
    body = json.loads(request.body)
    nodo = T_PlantillaNodo.objects.get(id=nodo_id)
    nodo.roles_visibles = body.get("roles_visibles")
    nodo.roles_editables = body.get("roles_editables")
    nodo.save(update_fields=["roles_visibles", "roles_editables"])
    return JsonResponse({
        "id": nodo.id,
        "roles_visibles": nodo.roles_visibles,
        "roles_editables": nodo.roles_editables,
    })


# --- Version API ---

@plantilla_admin_required
@require_POST
def api_guardar_version(request):
    body = json.loads(request.body)
    descripcion = body.get("descripcion", "")
    auto_aplicar = body.get("auto_aplicar_nuevas", False)
    version = guardar_version(descripcion, auto_aplicar, request.user)
    return JsonResponse({
        "version": version.version,
        "descripcion": version.descripcion,
        "fecha": version.fecha.isoformat(),
    })


@plantilla_admin_required
@require_GET
def api_versiones(request):
    versiones = T_PlantillaVersion.objects.all().order_by("-version")[:50]
    data = [{
        "id": v.id,
        "version": v.version,
        "descripcion": v.descripcion,
        "auto_aplicar_nuevas": v.auto_aplicar_nuevas,
        "fecha": v.fecha.isoformat(),
        "usuario": v.usuario.username if v.usuario else None,
    } for v in versiones]
    return JsonResponse(data, safe=False)


@plantilla_admin_required
@require_GET
def api_version_snapshot(request, version_id):
    version = T_PlantillaVersion.objects.get(id=version_id)
    return JsonResponse({
        "version": version.version,
        "descripcion": version.descripcion,
        "snapshot": version.snapshot,
        "fecha": version.fecha.isoformat(),
        "usuario": version.usuario.username if version.usuario else None,
    })


@plantilla_admin_required
@require_POST
def api_restaurar_version(request, version_id):
    nueva = restaurar_version(version_id, request.user)
    return JsonResponse({
        "version": nueva.version,
        "descripcion": nueva.descripcion,
    })


# --- Apply API ---

@plantilla_admin_required
@require_GET
def api_cortes(request):
    cortes = (T_ficha.objects.exclude(corte__isnull=True)
              .exclude(corte="")
              .values_list("corte", flat=True)
              .distinct()
              .order_by("corte"))
    return JsonResponse(list(cortes), safe=False)


@plantilla_admin_required
@require_POST
def api_preview_aplicar(request):
    body = json.loads(request.body)
    version_id = body.get("version_id")
    modo = body.get("modo")
    valor = body.get("valor")

    if not version_id:
        latest = T_PlantillaVersion.objects.order_by("-version").first()
        if not latest:
            return JsonResponse({"error": "No hay versiones guardadas"}, status=400)
        version_id = latest.id

    fichas_qs = obtener_fichas_por_seleccion(modo, valor)
    resumen = preview_aplicar(version_id, fichas_qs)
    return JsonResponse(resumen)


@plantilla_admin_required
@require_POST
def api_ejecutar_aplicar(request):
    body = json.loads(request.body)
    version_id = body.get("version_id")
    modo = body.get("modo")
    valor = body.get("valor")

    if not version_id:
        latest = T_PlantillaVersion.objects.order_by("-version").first()
        if not latest:
            return JsonResponse({"error": "No hay versiones guardadas"}, status=400)
        version_id = latest.id

    fichas_qs = obtener_fichas_por_seleccion(modo, valor)
    resultados = ejecutar_aplicar(version_id, fichas_qs, request.user)
    return JsonResponse({"resultados": resultados})


# --- Log API ---

@plantilla_admin_required
@require_GET
def api_log(request):
    qs = T_PlantillaAplicacion.objects.select_related("version", "ficha", "usuario")

    corte = request.GET.get("corte")
    if corte:
        qs = qs.filter(ficha__corte=corte)

    usuario = request.GET.get("usuario")
    if usuario:
        qs = qs.filter(usuario__username=usuario)

    registros = []
    for r in qs.order_by("-fecha")[:200]:
        registros.append({
            "version": r.version.version,
            "ficha_num": r.ficha.num,
            "resultado": r.resultado,
            "detalle": r.detalle,
            "fecha": r.fecha.isoformat(),
            "usuario": r.usuario.username if r.usuario else None,
        })
    return JsonResponse(registros, safe=False)
