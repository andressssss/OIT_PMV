# Modulo de Plantillas de Estructura Documental (Fichas) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an admin module that replaces hardcoded Python folder structures with a DB-backed template system, allowing admins to edit, version, and apply document tree structures to fichas with role-based visibility and full audit trail.

**Architecture:** New MPTT-based template models in `commons`, a new `plantillas` Django app for views/templates/JS, and targeted modifications to existing `obtener_carpetas` and ficha creation flows. Wunderbaum for the admin tree editor; existing JS manual rendering untouched.

**Tech Stack:** Django 5.1, django-mptt, Wunderbaum (CDN), Bootstrap 5, jQuery, existing permission system (PermisosMixin + T_permi)

**Spec:** `docs/superpowers/specs/2026-04-12-modulo-plantillas-estructura-fichas-design.md`

---

## File Structure

### New files (plantillas app)

| File | Responsibility |
|---|---|
| `plantillas/__init__.py` | App init |
| `plantillas/apps.py` | App config |
| `plantillas/urls.py` | URL patterns for the module |
| `plantillas/views.py` | Views: editor, historial, aplicar, log |
| `plantillas/decorators.py` | `@plantilla_admin_required` access control |
| `plantillas/services.py` | Core logic: reconciliation, snapshot, version management |
| `plantillas/templates/plantillas/editor.html` | Wunderbaum tree editor |
| `plantillas/templates/plantillas/historial.html` | Version history table |
| `plantillas/templates/plantillas/aplicar.html` | Apply template to fichas |
| `plantillas/templates/plantillas/log.html` | Application log |
| `static/js/plantillas/editor.js` | Wunderbaum editor logic |
| `static/js/plantillas/aplicar.js` | Apply UI logic (preview, execute) |
| `static/css/plantillas/editor.css` | Editor styles |

### Modified files

| File | Change |
|---|---|
| `commons/models.py` | Add 4 new models + 3 fields on T_DocumentFolder + 1 field on T_ficha |
| `commons/migrations/XXXX_*.py` | Schema + data migrations |
| `IOTPMV/settings/base.py` | Add `plantillas` to INSTALLED_APPS |
| `IOTPMV/urls.py` | Include plantillas URLs |
| `templates/base.html` | Add "Plantillas" nav item for authorized admins |
| `formacion/views.py` | Modify `obtener_carpetas` for visibility/permission filtering |
| `static/js/formacion/panel_ficha.js` | Respect `can_edit_folder` per node |
| `matricula/scripts/cargar_tree.py` | Use plantilla instead of hardcoded dict |
| `formacion/views.py` (crear ficha) | Hook auto-apply after ficha creation |
| `api/views/formacion.py` (crear ficha masivo) | Hook auto-apply after ficha creation |
| `matricula/views.py` (formalizar grupo) | Hook auto-apply after ficha creation |

---

## Task 1: Create plantillas app and new models

**Files:**
- Create: `plantillas/__init__.py`, `plantillas/apps.py`
- Modify: `commons/models.py:991` (append new models)
- Modify: `IOTPMV/settings/base.py:29` (add to INSTALLED_APPS)

- [ ] **Step 1: Create the plantillas app directory**

```bash
mkdir -p plantillas
```

- [ ] **Step 2: Create `plantillas/__init__.py`**

Empty file.

- [ ] **Step 3: Create `plantillas/apps.py`**

```python
from django.apps import AppConfig


class PlantillasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plantillas'
```

- [ ] **Step 4: Add new models to `commons/models.py`**

Append after line 990 (end of file):

```python
class T_PlantillaNodo(MPTTModel):
    class Meta:
        managed = True
        db_table = 't_plantilla_nodo'
    name = models.CharField(max_length=255)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='plantilla_children')
    orden = models.IntegerField(default=0)
    roles_visibles = models.JSONField(null=True, blank=True)
    roles_editables = models.JSONField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    fecha_crea = models.DateTimeField(auto_now_add=True)
    usuario_crea = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class MPTTMeta:
        order_insertion_by = ['orden']

    def __str__(self):
        return self.name


class T_PlantillaVersion(models.Model):
    class Meta:
        managed = True
        db_table = 't_plantilla_version'
        ordering = ['-version']
    version = models.IntegerField()
    snapshot = models.JSONField()
    descripcion = models.CharField(max_length=500)
    auto_aplicar_nuevas = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"v{self.version} - {self.descripcion}"


class T_PlantillaAplicacion(models.Model):
    class Meta:
        managed = True
        db_table = 't_plantilla_aplicacion'
        ordering = ['-fecha']
    version = models.ForeignKey(T_PlantillaVersion, on_delete=models.CASCADE)
    ficha = models.ForeignKey(T_ficha, on_delete=models.CASCADE)
    resultado = models.CharField(max_length=50)
    detalle = models.JSONField()
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"v{self.version.version} → Ficha {self.ficha.num} ({self.resultado})"


class T_PlantillaAdmin(models.Model):
    class Meta:
        managed = True
        db_table = 't_plantilla_admin'
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username
```

- [ ] **Step 5: Add fields to T_DocumentFolder**

At `commons/models.py:607` (inside T_DocumentFolder class), add after the `documento` field:

```python
    oculto = models.BooleanField(default=False)
    roles_visibles = models.JSONField(null=True, blank=True)
    roles_editables = models.JSONField(null=True, blank=True)
```

- [ ] **Step 6: Add `corte` field to T_ficha**

At `commons/models.py:335` (inside T_ficha class), add after the `vige` field:

```python
    corte = models.CharField(max_length=20, null=True, blank=True)
```

- [ ] **Step 7: Add `plantillas` to INSTALLED_APPS**

In `IOTPMV/settings/base.py`, add `'plantillas'` to the INSTALLED_APPS list (after `'administracion'`).

- [ ] **Step 8: Generate and run migrations**

```bash
python manage.py makemigrations commons
python manage.py makemigrations plantillas
python manage.py migrate
```

Expected: Migrations apply successfully, 4 new tables created, 4 fields added to existing tables.

- [ ] **Step 9: Commit**

```bash
git add commons/models.py commons/migrations/ plantillas/ IOTPMV/settings/base.py
git commit -m "feat: add plantilla models, T_DocumentFolder visibility fields, T_ficha.corte"
```

---

## Task 2: Data migration — load current structure as plantilla v1

**Files:**
- Create: `commons/management/commands/cargar_plantilla_inicial.py`

- [ ] **Step 1: Create the management command**

Create `commons/management/commands/cargar_plantilla_inicial.py`:

```python
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
```

- [ ] **Step 2: Run the command**

```bash
python manage.py cargar_plantilla_inicial
```

Expected: `Plantilla v1 creada: 39 nodos cargados`

- [ ] **Step 3: Commit**

```bash
git add commons/management/commands/cargar_plantilla_inicial.py
git commit -m "feat: add management command to load initial plantilla v1 from hardcoded structure"
```

---

## Task 3: Access control decorator and URL setup

**Files:**
- Create: `plantillas/decorators.py`
- Create: `plantillas/urls.py`
- Modify: `IOTPMV/urls.py:18`

- [ ] **Step 1: Create the decorator**

Create `plantillas/decorators.py`:

```python
from functools import wraps
from django.http import JsonResponse
from django.shortcuts import redirect
from commons.models import T_PlantillaAdmin


def plantilla_admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('signin')
        if not T_PlantillaAdmin.objects.filter(user=request.user).exists():
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            if is_ajax or request.content_type == 'application/json':
                return JsonResponse({"error": "No autorizado"}, status=403)
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper
```

- [ ] **Step 2: Create URL patterns**

Create `plantillas/urls.py`:

```python
from django.urls import path
from plantillas import views

urlpatterns = [
    path('', views.editor, name='plantillas_editor'),
    path('historial/', views.historial, name='plantillas_historial'),
    path('aplicar/', views.aplicar, name='plantillas_aplicar'),
    path('log/', views.log_aplicaciones, name='plantillas_log'),

    # API endpoints
    path('api/nodos/', views.api_obtener_nodos, name='plantillas_api_nodos'),
    path('api/nodo/crear/', views.api_crear_nodo, name='plantillas_api_crear_nodo'),
    path('api/nodo/<int:nodo_id>/editar/', views.api_editar_nodo, name='plantillas_api_editar_nodo'),
    path('api/nodo/<int:nodo_id>/mover/', views.api_mover_nodo, name='plantillas_api_mover_nodo'),
    path('api/nodo/<int:nodo_id>/toggle/', views.api_toggle_nodo, name='plantillas_api_toggle_nodo'),
    path('api/nodo/<int:nodo_id>/visibilidad/', views.api_visibilidad_nodo, name='plantillas_api_visibilidad_nodo'),
    path('api/guardar_version/', views.api_guardar_version, name='plantillas_api_guardar_version'),
    path('api/version/<int:version_id>/snapshot/', views.api_version_snapshot, name='plantillas_api_version_snapshot'),
    path('api/version/<int:version_id>/restaurar/', views.api_restaurar_version, name='plantillas_api_restaurar_version'),
    path('api/preview_aplicar/', views.api_preview_aplicar, name='plantillas_api_preview_aplicar'),
    path('api/ejecutar_aplicar/', views.api_ejecutar_aplicar, name='plantillas_api_ejecutar_aplicar'),
    path('api/log/', views.api_log, name='plantillas_api_log'),
    path('api/cortes/', views.api_cortes, name='plantillas_api_cortes'),
]
```

- [ ] **Step 3: Include in main URL config**

In `IOTPMV/urls.py`, add after line 18 (`path('api/', include('api.urls')),`):

```python
    path('plantillas/', include('plantillas.urls')),
```

And add `include` to the imports if not already there (it is — line 2).

- [ ] **Step 4: Commit**

```bash
git add plantillas/decorators.py plantillas/urls.py IOTPMV/urls.py
git commit -m "feat: add plantillas URL routing and access control decorator"
```

---

## Task 4: Core services — snapshot, reconciliation, version management

**Files:**
- Create: `plantillas/services.py`

- [ ] **Step 1: Create `plantillas/services.py`**

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add plantillas/services.py
git commit -m "feat: add core plantilla services — snapshot, reconciliation, version management"
```

---

## Task 5: API views for the plantilla editor

**Files:**
- Create: `plantillas/views.py`

- [ ] **Step 1: Create `plantillas/views.py`**

```python
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
    for r in qs[:200]:
        registros.append({
            "version": r.version.version,
            "ficha_num": r.ficha.num,
            "resultado": r.resultado,
            "detalle": r.detalle,
            "fecha": r.fecha.isoformat(),
            "usuario": r.usuario.username if r.usuario else None,
        })
    return JsonResponse(registros, safe=False)
```

- [ ] **Step 2: Commit**

```bash
git add plantillas/views.py
git commit -m "feat: add plantillas views — page renders and full API for editor, versions, apply, log"
```

---

## Task 6: Templates — editor, historial, aplicar, log

**Files:**
- Create: `plantillas/templates/plantillas/editor.html`
- Create: `plantillas/templates/plantillas/historial.html`
- Create: `plantillas/templates/plantillas/aplicar.html`
- Create: `plantillas/templates/plantillas/log.html`

- [ ] **Step 1: Create template directory**

```bash
mkdir -p plantillas/templates/plantillas
```

- [ ] **Step 2: Create `editor.html`**

Create `plantillas/templates/plantillas/editor.html`:

```html
{% extends "base.html" %}
{% load static %}

{% block styles %}
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/wunderbaum@0/dist/wunderbaum.min.css" />
<link rel="stylesheet" href="{% static 'css/plantillas/editor.css' %}" />
{% endblock %}

{% block content %}
<div class="container-fluid mt-4">
  <div class="d-flex justify-content-between align-items-center mb-3">
    <h4><i class="bi bi-diagram-3 me-2"></i>Editor de Plantilla</h4>
    <div>
      <a href="{% url 'plantillas_historial' %}" class="btn btn-outline-secondary btn-sm me-1">
        <i class="bi bi-clock-history me-1"></i>Historial
      </a>
      <a href="{% url 'plantillas_aplicar' %}" class="btn btn-outline-primary btn-sm me-1">
        <i class="bi bi-play-circle me-1"></i>Aplicar
      </a>
      <a href="{% url 'plantillas_log' %}" class="btn btn-outline-info btn-sm">
        <i class="bi bi-journal-text me-1"></i>Log
      </a>
    </div>
  </div>

  <!-- Toolbar -->
  <div class="btn-group mb-3">
    <button id="btnAgregar" class="btn btn-success btn-sm"><i class="bi bi-plus-lg me-1"></i>Agregar hijo</button>
    <button id="btnRenombrar" class="btn btn-warning btn-sm"><i class="bi bi-pencil me-1"></i>Renombrar</button>
    <button id="btnToggle" class="btn btn-secondary btn-sm"><i class="bi bi-eye-slash me-1"></i>Ocultar/Mostrar</button>
    <button id="btnVisibilidad" class="btn btn-info btn-sm"><i class="bi bi-shield-lock me-1"></i>Visibilidad</button>
  </div>
  <button id="btnGuardar" class="btn btn-primary btn-sm ms-3"><i class="bi bi-save me-1"></i>Guardar version</button>

  <!-- Tree container -->
  <div id="plantillaTree" class="border rounded p-2" style="min-height: 400px;"></div>
</div>

<!-- Modal visibilidad -->
<div class="modal fade" id="modalVisibilidad" tabindex="-1">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">Configurar visibilidad</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        <p class="text-muted mb-2">Nodo: <strong id="visNodoName"></strong></p>
        <h6>Roles que VEN esta carpeta:</h6>
        <div id="checksVisibles" class="mb-3"></div>
        <h6>Roles que EDITAN esta carpeta:</h6>
        <div id="checksEditables"></div>
        <p class="text-muted small mt-2">Dejar todo desmarcado = todos los roles</p>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Cancelar</button>
        <button type="button" id="btnGuardarVisibilidad" class="btn btn-primary btn-sm">Guardar</button>
      </div>
    </div>
  </div>
</div>

<!-- Modal guardar version -->
<div class="modal fade" id="modalGuardarVersion" tabindex="-1">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">Guardar nueva version</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        <div class="mb-3">
          <label class="form-label">Descripcion del cambio</label>
          <textarea id="versionDescripcion" class="form-control" rows="3" placeholder="Ej: Se agrego carpeta X en nodo Y"></textarea>
        </div>
        <div class="form-check">
          <input class="form-check-input" type="checkbox" id="versionAutoAplicar">
          <label class="form-check-label" for="versionAutoAplicar">Aplicar automaticamente a fichas nuevas</label>
        </div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Cancelar</button>
        <button type="button" id="btnConfirmarGuardar" class="btn btn-primary btn-sm">Guardar</button>
      </div>
    </div>
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/wunderbaum@0/dist/wunderbaum.umd.min.js"></script>
<script src="{% static 'js/plantillas/editor.js' %}"></script>
{% endblock %}
```

- [ ] **Step 3: Create `historial.html`**

Create `plantillas/templates/plantillas/historial.html`:

```html
{% extends "base.html" %}
{% load static %}

{% block content %}
<div class="container mt-4">
  <div class="d-flex justify-content-between align-items-center mb-3">
    <h4><i class="bi bi-clock-history me-2"></i>Historial de versiones</h4>
    <a href="{% url 'plantillas_editor' %}" class="btn btn-outline-primary btn-sm">
      <i class="bi bi-arrow-left me-1"></i>Volver al editor
    </a>
  </div>
  <table class="table table-striped table-hover" id="tablaHistorial">
    <thead>
      <tr>
        <th>Version</th>
        <th>Descripcion</th>
        <th>Usuario</th>
        <th>Fecha</th>
        <th>Auto-aplicar</th>
        <th>Acciones</th>
      </tr>
    </thead>
    <tbody id="historialBody"></tbody>
  </table>
</div>

<!-- Modal ver snapshot -->
<div class="modal fade" id="modalSnapshot" tabindex="-1">
  <div class="modal-dialog modal-lg">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title" id="snapshotTitle">Version</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        <pre id="snapshotContent" style="max-height:500px; overflow:auto;"></pre>
      </div>
    </div>
  </div>
</div>

<script>
document.addEventListener("DOMContentLoaded", function() {
  fetch("{% url 'plantillas_api_nodos' %}")
  // We'll actually load versions from a simple endpoint. For now use snapshot API.
  // Load all versions
  loadVersiones();
});

function loadVersiones() {
  // Fetch all versions via log or direct query
  fetch("/plantillas/api/log/")
    .then(r => r.json())
    .then(data => {
      // We need a versions endpoint. For now, we'll build from snapshot.
    });
}

function getCookie(name) {
  let v = null;
  document.cookie.split(";").forEach(c => {
    c = c.trim();
    if (c.startsWith(name + "=")) v = decodeURIComponent(c.substring(name.length + 1));
  });
  return v;
}

document.addEventListener("DOMContentLoaded", function() {
  // Load versions by fetching each version's snapshot metadata
  // For simplicity, we'll add a dedicated versions list endpoint later.
  // For now, render from T_PlantillaVersion directly via template context.
  const tbody = document.getElementById("historialBody");
  tbody.innerHTML = '<tr><td colspan="6" class="text-center">Cargando...</td></tr>';

  fetch("/plantillas/api/log/")
    .then(r => r.json())
    .then(() => {
      // This will be populated once we add the versions list API
      tbody.innerHTML = '<tr><td colspan="6" class="text-muted text-center">Use el endpoint de versiones</td></tr>';
    });
});
</script>
{% endblock %}
```

**Note:** This is a scaffold. The historial will be fully functional once the versions list endpoint is wired. We'll refine this in a later step.

- [ ] **Step 4: Create `aplicar.html`**

Create `plantillas/templates/plantillas/aplicar.html`:

```html
{% extends "base.html" %}
{% load static %}

{% block content %}
<div class="container mt-4">
  <div class="d-flex justify-content-between align-items-center mb-3">
    <h4><i class="bi bi-play-circle me-2"></i>Aplicar plantilla a fichas</h4>
    <a href="{% url 'plantillas_editor' %}" class="btn btn-outline-primary btn-sm">
      <i class="bi bi-arrow-left me-1"></i>Volver al editor
    </a>
  </div>

  <div class="row">
    <div class="col-md-6">
      <div class="card mb-3">
        <div class="card-body">
          <h6>Seleccion de fichas</h6>
          <div class="mb-3">
            <label class="form-label">Modo de seleccion</label>
            <select id="modoSeleccion" class="form-select">
              <option value="todas">Todas las fichas</option>
              <option value="corte">Por corte</option>
              <option value="listado">Por listado de numeros</option>
            </select>
          </div>
          <div id="campoCorte" class="mb-3 d-none">
            <label class="form-label">Corte</label>
            <select id="selectCorte" class="form-select"></select>
          </div>
          <div id="campoListado" class="mb-3 d-none">
            <label class="form-label">Numeros de ficha (uno por linea o separados por coma)</label>
            <textarea id="listadoFichas" class="form-control" rows="5" placeholder="3018230&#10;3063704&#10;3032252"></textarea>
          </div>
          <button id="btnPreview" class="btn btn-outline-primary btn-sm">
            <i class="bi bi-search me-1"></i>Vista previa
          </button>
        </div>
      </div>
    </div>
    <div class="col-md-6">
      <div class="card mb-3">
        <div class="card-body">
          <h6>Vista previa</h6>
          <div id="previewResult"></div>
        </div>
      </div>
    </div>
  </div>

  <button id="btnAplicar" class="btn btn-primary d-none">
    <i class="bi bi-check-circle me-1"></i>Aplicar cambios
  </button>

  <div id="resultadoAplicacion" class="mt-3"></div>
</div>

<script src="{% static 'js/plantillas/aplicar.js' %}"></script>
{% endblock %}
```

- [ ] **Step 5: Create `log.html`**

Create `plantillas/templates/plantillas/log.html`:

```html
{% extends "base.html" %}
{% load static %}

{% block content %}
<div class="container mt-4">
  <div class="d-flex justify-content-between align-items-center mb-3">
    <h4><i class="bi bi-journal-text me-2"></i>Log de aplicaciones</h4>
    <a href="{% url 'plantillas_editor' %}" class="btn btn-outline-primary btn-sm">
      <i class="bi bi-arrow-left me-1"></i>Volver al editor
    </a>
  </div>

  <div class="row mb-3">
    <div class="col-md-3">
      <select id="filtroCorte" class="form-select form-select-sm">
        <option value="">Todos los cortes</option>
      </select>
    </div>
    <div class="col-md-3">
      <input id="filtroUsuario" class="form-control form-control-sm" placeholder="Filtrar por usuario" />
    </div>
    <div class="col-md-2">
      <button id="btnFiltrar" class="btn btn-outline-primary btn-sm">Filtrar</button>
    </div>
  </div>

  <table class="table table-striped table-hover" id="tablaLog">
    <thead>
      <tr>
        <th>Version</th>
        <th>Ficha</th>
        <th>Resultado</th>
        <th>Detalle</th>
        <th>Usuario</th>
        <th>Fecha</th>
      </tr>
    </thead>
    <tbody id="logBody"></tbody>
  </table>
</div>

<script>
function getCookie(name) {
  let v = null;
  document.cookie.split(";").forEach(c => {
    c = c.trim();
    if (c.startsWith(name + "=")) v = decodeURIComponent(c.substring(name.length + 1));
  });
  return v;
}

function cargarLog(params = "") {
  const tbody = document.getElementById("logBody");
  tbody.innerHTML = '<tr><td colspan="6" class="text-center">Cargando...</td></tr>';

  fetch(`/plantillas/api/log/?${params}`)
    .then(r => r.json())
    .then(data => {
      if (!data.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-muted text-center">Sin registros</td></tr>';
        return;
      }
      tbody.innerHTML = data.map(r => `
        <tr>
          <td>v${r.version}</td>
          <td>${r.ficha_num}</td>
          <td><span class="badge bg-${r.resultado === 'exitoso' ? 'success' : 'danger'}">${r.resultado}</span></td>
          <td><small>${JSON.stringify(r.detalle)}</small></td>
          <td>${r.usuario || '-'}</td>
          <td>${new Date(r.fecha).toLocaleString()}</td>
        </tr>
      `).join("");
    });
}

document.addEventListener("DOMContentLoaded", function() {
  cargarLog();

  fetch("/plantillas/api/cortes/")
    .then(r => r.json())
    .then(cortes => {
      const sel = document.getElementById("filtroCorte");
      cortes.forEach(c => {
        const opt = document.createElement("option");
        opt.value = c;
        opt.textContent = c;
        sel.appendChild(opt);
      });
    });

  document.getElementById("btnFiltrar").addEventListener("click", function() {
    const corte = document.getElementById("filtroCorte").value;
    const usuario = document.getElementById("filtroUsuario").value;
    const params = new URLSearchParams();
    if (corte) params.set("corte", corte);
    if (usuario) params.set("usuario", usuario);
    cargarLog(params.toString());
  });
});
</script>
{% endblock %}
```

- [ ] **Step 6: Commit**

```bash
git add plantillas/templates/
git commit -m "feat: add plantillas templates — editor, historial, aplicar, log"
```

---

## Task 7: Frontend JavaScript — editor and aplicar

**Files:**
- Create: `static/js/plantillas/editor.js`
- Create: `static/js/plantillas/aplicar.js`
- Create: `static/css/plantillas/editor.css`

- [ ] **Step 1: Create directories**

```bash
mkdir -p static/js/plantillas static/css/plantillas
```

- [ ] **Step 2: Create `static/css/plantillas/editor.css`**

```css
.nodo-inactivo > .wb-row {
  opacity: 0.4;
  text-decoration: line-through;
}

#plantillaTree .wb-row:hover {
  background-color: #f0f4ff;
}

#plantillaTree {
  font-size: 0.9rem;
}
```

- [ ] **Step 3: Create `static/js/plantillas/editor.js`**

```javascript
const ROLES = ["admin", "instructor", "aprendiz", "lider", "gestor", "consulta", "cuentas"];

let tree = null;

function getCookie(name) {
  let v = null;
  document.cookie.split(";").forEach(c => {
    c = c.trim();
    if (c.startsWith(name + "=")) v = decodeURIComponent(c.substring(name.length + 1));
  });
  return v;
}

function apiCall(url, method, body) {
  const opts = {
    method,
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"),
    },
  };
  if (body) opts.body = JSON.stringify(body);
  return fetch(url, opts).then(r => r.json());
}

document.addEventListener("DOMContentLoaded", function () {
  tree = new mar10.Wunderbaum({
    element: document.getElementById("plantillaTree"),
    id: "plantillaEditor",
    source: { url: "/plantillas/api/nodos/" },
    types: {},
    dnd: {
      dragStart: () => true,
      dragEnter: () => true,
      drop: (e) => {
        const node = e.node;
        const targetNode = e.region === "over" ? e.targetNode : e.targetNode.parent;
        const parentId = targetNode ? targetNode.key : null;

        // Calculate new orden based on position
        const siblings = targetNode ? targetNode.children : tree.root.children;
        const idx = siblings ? siblings.indexOf(node) : 0;

        apiCall(`/plantillas/api/nodo/${node.key}/mover/`, "POST", {
          parent_id: parentId ? parseInt(parentId) : null,
          orden: idx,
        });
      },
    },
    activate: (e) => {
      // Node selected — enable toolbar buttons
    },
    render: (e) => {
      const node = e.node;
      if (node.data && !node.data.activo) {
        if (e.nodeElem) e.nodeElem.classList.add("nodo-inactivo");
      }
    },
  });

  // --- Toolbar actions ---

  document.getElementById("btnAgregar").addEventListener("click", function () {
    const node = tree.getActiveNode();
    if (!node) { alert("Selecciona un nodo primero"); return; }

    const nombre = prompt("Nombre de la nueva carpeta:");
    if (!nombre) return;

    apiCall("/plantillas/api/nodo/crear/", "POST", {
      parent_id: parseInt(node.key),
      name: nombre,
    }).then((data) => {
      node.addChildren({
        title: data.name,
        key: String(data.id),
        data: { id: data.id, orden: data.orden, activo: true, roles_visibles: null, roles_editables: null },
        expanded: true,
        children: [],
      });
      node.setExpanded(true);
    });
  });

  document.getElementById("btnRenombrar").addEventListener("click", function () {
    const node = tree.getActiveNode();
    if (!node) { alert("Selecciona un nodo primero"); return; }

    const nombre = prompt("Nuevo nombre:", node.title);
    if (!nombre || nombre === node.title) return;

    apiCall(`/plantillas/api/nodo/${node.key}/editar/`, "POST", { name: nombre })
      .then(() => {
        node.setTitle(nombre);
      });
  });

  document.getElementById("btnToggle").addEventListener("click", function () {
    const node = tree.getActiveNode();
    if (!node) { alert("Selecciona un nodo primero"); return; }

    apiCall(`/plantillas/api/nodo/${node.key}/toggle/`, "POST")
      .then((data) => {
        node.data.activo = data.activo;
        if (data.activo) {
          node.removeClass("nodo-inactivo");
        } else {
          node.addClass("nodo-inactivo");
        }
      });
  });

  // --- Visibilidad modal ---

  document.getElementById("btnVisibilidad").addEventListener("click", function () {
    const node = tree.getActiveNode();
    if (!node) { alert("Selecciona un nodo primero"); return; }

    document.getElementById("visNodoName").textContent = node.title;
    renderCheckboxes("checksVisibles", node.data.roles_visibles);
    renderCheckboxes("checksEditables", node.data.roles_editables);

    new bootstrap.Modal(document.getElementById("modalVisibilidad")).show();
  });

  document.getElementById("btnGuardarVisibilidad").addEventListener("click", function () {
    const node = tree.getActiveNode();
    const visibles = getCheckedRoles("checksVisibles");
    const editables = getCheckedRoles("checksEditables");

    apiCall(`/plantillas/api/nodo/${node.key}/visibilidad/`, "POST", {
      roles_visibles: visibles.length ? visibles : null,
      roles_editables: editables.length ? editables : null,
    }).then((data) => {
      node.data.roles_visibles = data.roles_visibles;
      node.data.roles_editables = data.roles_editables;
      bootstrap.Modal.getInstance(document.getElementById("modalVisibilidad")).hide();
    });
  });

  // --- Guardar version ---

  document.getElementById("btnGuardar").addEventListener("click", function () {
    new bootstrap.Modal(document.getElementById("modalGuardarVersion")).show();
  });

  document.getElementById("btnConfirmarGuardar").addEventListener("click", function () {
    const descripcion = document.getElementById("versionDescripcion").value;
    const autoAplicar = document.getElementById("versionAutoAplicar").checked;

    if (!descripcion.trim()) { alert("Ingresa una descripcion"); return; }

    apiCall("/plantillas/api/guardar_version/", "POST", {
      descripcion,
      auto_aplicar_nuevas: autoAplicar,
    }).then((data) => {
      bootstrap.Modal.getInstance(document.getElementById("modalGuardarVersion")).hide();
      document.getElementById("versionDescripcion").value = "";
      document.getElementById("versionAutoAplicar").checked = false;
      Toastify({
        text: `Version v${data.version} guardada`,
        duration: 3000,
        gravity: "top",
        position: "right",
        backgroundColor: "#198754",
      }).showToast();
    });
  });
});

function renderCheckboxes(containerId, selectedRoles) {
  const container = document.getElementById(containerId);
  container.innerHTML = ROLES.map(rol => {
    const checked = selectedRoles && selectedRoles.includes(rol) ? "checked" : "";
    return `<div class="form-check form-check-inline">
      <input class="form-check-input" type="checkbox" value="${rol}" ${checked} id="${containerId}_${rol}">
      <label class="form-check-label" for="${containerId}_${rol}">${rol}</label>
    </div>`;
  }).join("");
}

function getCheckedRoles(containerId) {
  const checks = document.querySelectorAll(`#${containerId} input:checked`);
  return Array.from(checks).map(c => c.value);
}
```

- [ ] **Step 4: Create `static/js/plantillas/aplicar.js`**

```javascript
function getCookie(name) {
  let v = null;
  document.cookie.split(";").forEach(c => {
    c = c.trim();
    if (c.startsWith(name + "=")) v = decodeURIComponent(c.substring(name.length + 1));
  });
  return v;
}

function apiCall(url, method, body) {
  const opts = {
    method,
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"),
    },
  };
  if (body) opts.body = JSON.stringify(body);
  return fetch(url, opts).then(r => r.json());
}

document.addEventListener("DOMContentLoaded", function () {
  const modoSelect = document.getElementById("modoSeleccion");
  const campoCorte = document.getElementById("campoCorte");
  const campoListado = document.getElementById("campoListado");

  // Load cortes
  fetch("/plantillas/api/cortes/")
    .then(r => r.json())
    .then(cortes => {
      const sel = document.getElementById("selectCorte");
      cortes.forEach(c => {
        const opt = document.createElement("option");
        opt.value = c;
        opt.textContent = c;
        sel.appendChild(opt);
      });
    });

  modoSelect.addEventListener("change", function () {
    campoCorte.classList.toggle("d-none", this.value !== "corte");
    campoListado.classList.toggle("d-none", this.value !== "listado");
  });

  // Preview
  document.getElementById("btnPreview").addEventListener("click", function () {
    const modo = modoSelect.value;
    let valor = null;
    if (modo === "corte") valor = document.getElementById("selectCorte").value;
    if (modo === "listado") valor = document.getElementById("listadoFichas").value;

    const previewDiv = document.getElementById("previewResult");
    previewDiv.innerHTML = '<div class="text-center"><div class="spinner-border spinner-border-sm"></div> Calculando...</div>';

    // Get latest version
    apiCall("/plantillas/api/guardar_version/", "POST", {
      descripcion: "__preview_temp__",
      auto_aplicar_nuevas: false,
    }).then(versionData => {
      // Actually we should use existing version. Let's get from a simpler approach.
      // For preview, use latest version.
      apiCall("/plantillas/api/preview_aplicar/", "POST", {
        version_id: null, // will use latest
        modo,
        valor,
      }).then(data => {
        document.getElementById("btnAplicar").classList.remove("d-none");
        previewDiv.innerHTML = `
          <p><strong>Total fichas:</strong> ${data.total_fichas}</p>
          ${data.fichas_preview.map(f => `
            <div class="border rounded p-2 mb-2">
              <strong>Ficha ${f.ficha_num}</strong>
              <br><span class="text-success">Crear: ${f.nodos_a_crear.length ? f.nodos_a_crear.join(", ") : "ninguno"}</span>
              <br><span class="text-warning">Ocultar: ${f.nodos_a_ocultar.length ? f.nodos_a_ocultar.join(", ") : "ninguno"}</span>
              <br><span class="text-info">Sincronizar: ${f.nodos_a_sincronizar.length ? f.nodos_a_sincronizar.join(", ") : "ninguno"}</span>
            </div>
          `).join("")}
          ${data.total_fichas > 10 ? `<p class="text-muted">Mostrando 10 de ${data.total_fichas} fichas</p>` : ""}
        `;
      });
    });
  });

  // Apply
  document.getElementById("btnAplicar").addEventListener("click", function () {
    if (!confirm("Estas seguro de aplicar los cambios? Esta accion es irreversible.")) return;

    const modo = modoSelect.value;
    let valor = null;
    if (modo === "corte") valor = document.getElementById("selectCorte").value;
    if (modo === "listado") valor = document.getElementById("listadoFichas").value;

    const resultDiv = document.getElementById("resultadoAplicacion");
    resultDiv.innerHTML = '<div class="text-center"><div class="spinner-border"></div> Aplicando...</div>';

    apiCall("/plantillas/api/ejecutar_aplicar/", "POST", {
      version_id: null, // latest
      modo,
      valor,
    }).then(data => {
      const exitosos = data.resultados.filter(r => r.resultado === "exitoso").length;
      const errores = data.resultados.filter(r => r.resultado === "error").length;

      resultDiv.innerHTML = `
        <div class="alert alert-${errores ? 'warning' : 'success'}">
          <strong>Aplicacion completada</strong><br>
          Exitosos: ${exitosos} | Errores: ${errores}
        </div>
        ${data.resultados.map(r => `
          <div class="border rounded p-2 mb-1">
            <span class="badge bg-${r.resultado === 'exitoso' ? 'success' : 'danger'}">${r.resultado}</span>
            Ficha ${r.ficha_num}:
            ${r.detalle.creados ? r.detalle.creados.length + " creados" : ""}
            ${r.detalle.ocultados ? r.detalle.ocultados.length + " ocultados" : ""}
            ${r.detalle.sincronizados ? r.detalle.sincronizados.length + " sincronizados" : ""}
          </div>
        `).join("")}
      `;
    });
  });
});
```

- [ ] **Step 5: Commit**

```bash
git add static/js/plantillas/ static/css/plantillas/
git commit -m "feat: add frontend JS/CSS for plantilla editor (Wunderbaum) and apply UI"
```

---

## Task 8: Add "Plantillas" to navigation menu

**Files:**
- Modify: `templates/base.html:109`

- [ ] **Step 1: Add nav item for plantilla admins**

In `templates/base.html`, after line 128 (end of the admin Informes dropdown `</li>`), add:

```html
                  {% if is_plantilla_admin %}
                  <li class="nav-item">
                    <a class="nav-link" href="{% url 'plantillas_editor' %}"><i class="bi bi-diagram-3 me-1"></i>Plantillas</a>
                  </li>
                  {% endif %}
```

- [ ] **Step 2: Add context processor to inject `is_plantilla_admin`**

Create `plantillas/context_processors.py`:

```python
from commons.models import T_PlantillaAdmin


def plantilla_admin(request):
    if request.user.is_authenticated:
        return {
            "is_plantilla_admin": T_PlantillaAdmin.objects.filter(user=request.user).exists()
        }
    return {"is_plantilla_admin": False}
```

- [ ] **Step 3: Register context processor**

In `IOTPMV/settings/base.py`, find the `TEMPLATES` setting and add `'plantillas.context_processors.plantilla_admin'` to the `context_processors` list.

- [ ] **Step 4: Commit**

```bash
git add templates/base.html plantillas/context_processors.py IOTPMV/settings/base.py
git commit -m "feat: add Plantillas nav item for authorized admins"
```

---

## Task 9: Modify obtener_carpetas to respect visibility fields

**Files:**
- Modify: `formacion/views.py:80-132`
- Modify: `static/js/formacion/panel_ficha.js:204` (renderTree)

- [ ] **Step 1: Update `obtener_carpetas` in `formacion/views.py`**

Replace the function at lines 80-132 with:

```python
@login_required
def obtener_carpetas(request, ficha_id):
    """ Obtener todas las carpetas y documentos asociados a la ficha """

    ficha_vige = T_ficha.objects.filter(id=ficha_id).values_list("vige", flat=True).first()

    nodos = T_DocumentFolder.objects.filter(ficha_id=ficha_id).values(
        "id", "name", "parent_id", "tipo",
        "documento__id", "documento__nom", "documento__archi",
        "oculto", "roles_visibles", "roles_editables"
    )

    # Filtro por vigencia
    if ficha_vige == "2025":
        nodos = [n for n in nodos if n["name"] not in ["3. EJECUCIÓN", "4. EVALUACIÓN"]]

    # Obtener rol del usuario
    perfil = T_perfil.objects.filter(user=request.user).first()
    rol_usuario = perfil.rol if perfil else None

    # Filtrar nodos ocultos y por visibilidad de rol
    nodos_filtrados = []
    for n in nodos:
        if n["oculto"]:
            continue
        rv = n["roles_visibles"]
        if rv and rol_usuario and rol_usuario not in rv:
            continue
        nodos_filtrados.append(n)

    mixin = PermisosMixin()
    acciones = mixin.get_permission_actions_for(request, "portafolios")
    can_edit = acciones.get("editar", False)

    folder_map = {}

    for nodo in nodos_filtrados:
        nodo_id = nodo["id"]
        parent_id = nodo["parent_id"]

        # Determinar si el usuario puede editar esta carpeta
        re = nodo["roles_editables"]
        can_edit_folder = can_edit
        if re and rol_usuario and rol_usuario not in re:
            can_edit_folder = False

        nodo_data = {
            "id": nodo_id,
            "name": nodo["name"],
            "parent_id": parent_id,
            "tipo": nodo["tipo"],
            "can_edit_folder": can_edit_folder,
            "children": []
        }

        if nodo["tipo"] == "documento":
            nodo_data.update({
                "documento_id": nodo["documento__id"],
                "documento_nombre": nodo["documento__nom"],
                "url": nodo["documento__archi"],
            })

        folder_map[nodo_id] = nodo_data

    root_nodes = []

    for nodo in folder_map.values():
        parent_id = nodo["parent_id"]
        if parent_id:
            if parent_id in folder_map:
                folder_map[parent_id]["children"].append(nodo)
        else:
            root_nodes.append(nodo)

    return JsonResponse({
        'can_edit': can_edit,
        'nodos': root_nodes
    }, safe=False)
```

Add the T_perfil import at the top of `formacion/views.py` if not already there:

```python
from commons.models import T_perfil
```

- [ ] **Step 2: Update `renderTree` in `panel_ficha.js`**

In `static/js/formacion/panel_ficha.js`, inside the `renderTree()` function (around line 204), find the section where the upload button is rendered for folders. The upload button ("Cargar documento") should check `node.can_edit_folder` instead of (or in addition to) the global `canEdit`. Look for the block that creates the upload `<li>` element and wrap it with:

```javascript
if (canEdit && node.can_edit_folder !== false) {
    // ... existing upload button code
}
```

This ensures that folders with restricted editing still show the tree structure but hide upload/delete actions.

- [ ] **Step 3: Commit**

```bash
git add formacion/views.py static/js/formacion/panel_ficha.js
git commit -m "feat: filter document tree by oculto, roles_visibles, roles_editables"
```

---

## Task 10: Hook auto-apply to ficha creation flows

**Files:**
- Modify: `matricula/scripts/cargar_tree.py:59-62`
- Modify: `formacion/views.py:1249`
- Modify: `api/views/formacion.py:284` (after ficha creation)
- Modify: `matricula/views.py:1261` (after ficha creation)

- [ ] **Step 1: Update `matricula/scripts/cargar_tree.py`**

Replace `crear_datos_prueba` function (lines 59-62) with:

```python
def crear_datos_prueba(ficha_id):
    from plantillas.services import aplicar_a_ficha_nueva
    ficha = T_ficha.objects.get(id=ficha_id)
    result = aplicar_a_ficha_nueva(ficha)
    if result is None:
        # Fallback: no auto-apply version exists, use hardcoded structure
        crear_estructura_arbol(ficha, estructura_documental)
        print("Portafolio creado desde estructura hardcodeada (fallback).")
    else:
        print("Portafolio creado desde plantilla vigente.")
```

- [ ] **Step 2: Hook in `matricula/views.py`**

After line 1283 (`T_apre.objects.filter(grupo=grupo).update(ficha=ficha)`), add:

```python
            from plantillas.services import aplicar_a_ficha_nueva
            aplicar_a_ficha_nueva(ficha)
```

Also check if this flow already calls `crear_datos_prueba` — if it does, the fallback in Step 1 handles it. If it doesn't, add the hook here.

- [ ] **Step 3: Hook in `api/views/formacion.py`**

After the ficha creation block (around line 296), verify if `crear_datos_prueba` is called. If not, add:

```python
            from plantillas.services import aplicar_a_ficha_nueva
            aplicar_a_ficha_nueva(ficha)
```

- [ ] **Step 4: Commit**

```bash
git add matricula/scripts/cargar_tree.py formacion/views.py api/views/formacion.py matricula/views.py
git commit -m "feat: hook plantilla auto-apply to all ficha creation flows"
```

---

## Task 11: Add versions list API for historial view

**Files:**
- Modify: `plantillas/urls.py`
- Modify: `plantillas/views.py`
- Modify: `plantillas/templates/plantillas/historial.html`

- [ ] **Step 1: Add versions list endpoint**

In `plantillas/urls.py`, add:

```python
    path('api/versiones/', views.api_versiones, name='plantillas_api_versiones'),
```

- [ ] **Step 2: Add view function**

In `plantillas/views.py`, add:

```python
@plantilla_admin_required
@require_GET
def api_versiones(request):
    versiones = T_PlantillaVersion.objects.all()[:50]
    data = [{
        "id": v.id,
        "version": v.version,
        "descripcion": v.descripcion,
        "auto_aplicar_nuevas": v.auto_aplicar_nuevas,
        "fecha": v.fecha.isoformat(),
        "usuario": v.usuario.username if v.usuario else None,
    } for v in versiones]
    return JsonResponse(data, safe=False)
```

- [ ] **Step 3: Update historial template**

Replace the `<script>` block in `plantillas/templates/plantillas/historial.html` with:

```html
<script>
function getCookie(name) {
  let v = null;
  document.cookie.split(";").forEach(c => {
    c = c.trim();
    if (c.startsWith(name + "=")) v = decodeURIComponent(c.substring(name.length + 1));
  });
  return v;
}

document.addEventListener("DOMContentLoaded", function() {
  const tbody = document.getElementById("historialBody");

  fetch("/plantillas/api/versiones/")
    .then(r => r.json())
    .then(data => {
      if (!data.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-muted text-center">Sin versiones</td></tr>';
        return;
      }
      tbody.innerHTML = data.map(v => `
        <tr>
          <td><strong>v${v.version}</strong></td>
          <td>${v.descripcion}</td>
          <td>${v.usuario || '-'}</td>
          <td>${new Date(v.fecha).toLocaleString()}</td>
          <td>${v.auto_aplicar_nuevas ? '<span class="badge bg-success">Si</span>' : '-'}</td>
          <td>
            <button class="btn btn-outline-secondary btn-sm" onclick="verSnapshot(${v.id}, ${v.version})">Ver</button>
            <button class="btn btn-outline-warning btn-sm" onclick="restaurarVersion(${v.id}, ${v.version})">Restaurar</button>
          </td>
        </tr>
      `).join("");
    });
});

function verSnapshot(id, version) {
  fetch(`/plantillas/api/version/${id}/snapshot/`)
    .then(r => r.json())
    .then(data => {
      document.getElementById("snapshotTitle").textContent = `Version v${data.version} - ${data.descripcion}`;
      document.getElementById("snapshotContent").textContent = JSON.stringify(data.snapshot, null, 2);
      new bootstrap.Modal(document.getElementById("modalSnapshot")).show();
    });
}

function restaurarVersion(id, version) {
  if (!confirm(`Restaurar a version v${version}? Esto creara una nueva version basada en esa.`)) return;
  fetch(`/plantillas/api/version/${id}/restaurar/`, {
    method: "POST",
    headers: {"Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken")},
  })
    .then(r => r.json())
    .then(data => {
      alert(`Restaurada como v${data.version}`);
      location.reload();
    });
}
</script>
```

- [ ] **Step 4: Commit**

```bash
git add plantillas/urls.py plantillas/views.py plantillas/templates/plantillas/historial.html
git commit -m "feat: add versions list API and functional historial view"
```

---

## Task 12: Fix aplicar.js to use latest version properly

**Files:**
- Modify: `plantillas/views.py` (api_preview_aplicar, api_ejecutar_aplicar)
- Modify: `static/js/plantillas/aplicar.js`

- [ ] **Step 1: Update views to default to latest version**

In `plantillas/views.py`, modify `api_preview_aplicar` and `api_ejecutar_aplicar` to handle `version_id=null`:

In both functions, after `version_id = body.get("version_id")`, add:

```python
    if not version_id:
        latest = T_PlantillaVersion.objects.order_by("-version").first()
        if not latest:
            return JsonResponse({"error": "No hay versiones guardadas"}, status=400)
        version_id = latest.id
```

- [ ] **Step 2: Remove temp version creation from aplicar.js preview**

In `static/js/plantillas/aplicar.js`, replace the preview button handler to NOT create a temp version:

```javascript
  document.getElementById("btnPreview").addEventListener("click", function () {
    const modo = modoSelect.value;
    let valor = null;
    if (modo === "corte") valor = document.getElementById("selectCorte").value;
    if (modo === "listado") valor = document.getElementById("listadoFichas").value;

    const previewDiv = document.getElementById("previewResult");
    previewDiv.innerHTML = '<div class="text-center"><div class="spinner-border spinner-border-sm"></div> Calculando...</div>';

    apiCall("/plantillas/api/preview_aplicar/", "POST", {
      version_id: null,
      modo,
      valor,
    }).then(data => {
      if (data.error) {
        previewDiv.innerHTML = `<div class="alert alert-warning">${data.error}</div>`;
        return;
      }
      document.getElementById("btnAplicar").classList.remove("d-none");
      previewDiv.innerHTML = `
        <p><strong>Total fichas:</strong> ${data.total_fichas}</p>
        ${data.fichas_preview.map(f => `
          <div class="border rounded p-2 mb-2">
            <strong>Ficha ${f.ficha_num}</strong>
            <br><span class="text-success">Crear: ${f.nodos_a_crear.length ? f.nodos_a_crear.join(", ") : "ninguno"}</span>
            <br><span class="text-warning">Ocultar: ${f.nodos_a_ocultar.length ? f.nodos_a_ocultar.join(", ") : "ninguno"}</span>
            <br><span class="text-info">Sincronizar: ${f.nodos_a_sincronizar.length ? f.nodos_a_sincronizar.join(", ") : "ninguno"}</span>
          </div>
        `).join("")}
        ${data.total_fichas > 10 ? `<p class="text-muted">Mostrando 10 de ${data.total_fichas} fichas</p>` : ""}
      `;
    });
  });
```

- [ ] **Step 3: Commit**

```bash
git add plantillas/views.py static/js/plantillas/aplicar.js
git commit -m "fix: use latest version by default in preview/apply, remove temp version creation"
```

---

## Task 13: Register admin user and verify

- [ ] **Step 1: Create management command to add plantilla admins**

Create `commons/management/commands/agregar_plantilla_admin.py`:

```python
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from commons.models import T_PlantillaAdmin


class Command(BaseCommand):
    help = "Agrega un usuario a la lista de administradores de plantillas"

    def add_arguments(self, parser):
        parser.add_argument("--username", type=str, required=True)

    def handle(self, *args, **options):
        username = options["username"]
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"No existe el usuario '{username}'"))
            return

        admin, created = T_PlantillaAdmin.objects.get_or_create(user=user)
        if created:
            self.stdout.write(self.style.SUCCESS(f"'{username}' agregado como admin de plantillas"))
        else:
            self.stdout.write(self.style.WARNING(f"'{username}' ya es admin de plantillas"))
```

- [ ] **Step 2: Run initial setup**

```bash
python manage.py cargar_plantilla_inicial
python manage.py agregar_plantilla_admin --username <tu_username>
```

- [ ] **Step 3: Start dev server and verify**

```bash
python manage.py runserver 0.0.0.0:8000
```

Navigate to `/plantillas/` — the editor should load with the plantilla v1 tree in Wunderbaum.

Verify:
- Tree renders with all 39 nodes from the structure
- "Agregar hijo" creates a new node
- "Renombrar" renames inline
- "Ocultar/Mostrar" toggles node opacity
- "Visibilidad" opens modal with role checkboxes
- "Guardar version" creates a new version
- Navigation links to historial, aplicar, log work
- A non-admin user gets redirected when visiting `/plantillas/`

- [ ] **Step 4: Commit**

```bash
git add commons/management/commands/agregar_plantilla_admin.py
git commit -m "feat: add command to register plantilla admins, complete initial setup"
```
