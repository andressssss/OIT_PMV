# Módulo Usuarios de Consulta — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Crear el modelo `T_consulta`, el formulario, las 5 vistas CRUD, las URLs, el template y el JS para administrar usuarios de consulta desde el panel de admin, siguiendo el patrón exacto de `T_admin`/`administradores`.

**Architecture:** Opción A — replicar el patrón existente sin modificar código en uso. Cada archivo nuevo/editado tiene una sola responsabilidad. La card en el dashboard usa el permiso `consultas` como clave de visibilidad.

**Tech Stack:** Django 4.x, Bootstrap 5, Fetch API (vanilla JS), django.test

---

## File Map

| Acción | Archivo | Qué cambia |
|---|---|---|
| Modificar | `commons/models.py` | Agregar `T_consulta` después de `T_admin` |
| Crear | `commons/migrations/XXXX_t_consulta.py` | Generada por makemigrations |
| Modificar | `usuarios/forms.py` | Agregar `ConsultaForm`, importar `T_consulta` |
| Modificar | `commons/management/commands/poblar_permisos.py` | Agregar `consultas` a permisos de `admin` |
| Modificar | `usuarios/views.py` | Importar `T_consulta` + `ConsultaForm`, agregar 5 vistas, agregar card en `dashboard_admin` |
| Modificar | `IOTPMV/urls.py` | Agregar 5 rutas para consultas |
| Crear | `usuarios/templates/consulta.html` | Template lista + modales crear/editar |
| Crear | `static/js/usuarios/consulta.js` | JS para crear/editar/eliminar via fetch |
| Crear | `usuarios/tests/test_consulta.py` | Tests del módulo |

---

## Task 1: Modelo `T_consulta` y migración

**Files:**
- Modify: `commons/models.py` — después de línea ~120 (cierre de `T_admin`)
- Create: migración generada automáticamente

- [ ] **Step 1: Escribir el test**

Crear `usuarios/tests/__init__.py` (vacío si no existe) y `usuarios/tests/test_consulta.py`:

```python
from django.test import TestCase
from django.contrib.auth.models import User
from commons.models import T_perfil, T_consulta


class T_consultaModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testcon', password='1234')
        self.perfil = T_perfil.objects.create(
            user=self.user, nom='Ana', apelli='Lopez',
            tipo_dni='CC', dni=123456789, tele='3001234567',
            dire='Calle 1', mail='ana@test.com', gene='M',
            fecha_naci='1990-01-01', rol='consulta'
        )

    def test_crear_consulta(self):
        consulta = T_consulta.objects.create(
            perfil=self.perfil,
            area='sistemas',
            nivel_acceso='basico',
            esta='activo'
        )
        self.assertEqual(consulta.perfil, self.perfil)
        self.assertEqual(consulta.area, 'sistemas')
        self.assertEqual(consulta.nivel_acceso, 'basico')
        self.assertEqual(consulta.esta, 'activo')

    def test_str_consulta(self):
        consulta = T_consulta.objects.create(
            perfil=self.perfil, area='contable',
            nivel_acceso='intermedio', esta='activo'
        )
        self.assertIn('Ana', str(consulta))
```

- [ ] **Step 2: Ejecutar el test — debe fallar**

```bash
python manage.py test usuarios.tests.test_consulta -v 2
```
Esperado: `ImportError: cannot import name 'T_consulta'`

- [ ] **Step 3: Agregar `T_consulta` en `commons/models.py`**

Insertar después del bloque de `T_admin` (después de la línea `def __str__` de T_admin):

```python
class T_consulta(models.Model):
    class Meta:
        managed = True
        db_table = 't_consulta'

    AREA_CHOICES = [
        ('sistemas',  'Sistemas'),
        ('contable',  'Contable'),
        ('direccion', 'Dirección'),
        ('rrhh',      'RRHH'),
    ]
    NIVEL_CHOICES = [
        ('basico',     'Básico'),
        ('intermedio', 'Intermedio'),
        ('avanzado',   'Avanzado'),
    ]
    ESTADO_CHOICES = [
        ('activo',   'Activo'),
        ('inactivo', 'Inactivo'),
    ]
    perfil       = models.OneToOneField(T_perfil, on_delete=models.CASCADE, related_name='consulta')
    area         = models.CharField(max_length=20, choices=AREA_CHOICES)
    nivel_acceso = models.CharField(max_length=20, choices=NIVEL_CHOICES)
    esta         = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='activo')

    def __str__(self):
        return f"{self.perfil.nom} {self.perfil.apelli} - {self.get_area_display()} / {self.get_nivel_acceso_display()}"
```

- [ ] **Step 4: Generar y aplicar migración**

```bash
python manage.py makemigrations commons --name t_consulta
python manage.py migrate
```
Esperado: `Applying commons.XXXX_t_consulta... OK`

- [ ] **Step 5: Ejecutar el test — debe pasar**

```bash
python manage.py test usuarios.tests.test_consulta -v 2
```
Esperado: `OK (2 tests)`

- [ ] **Step 6: Commit**

```bash
git add commons/models.py commons/migrations/ usuarios/tests/
git commit -m "feat: add T_consulta model with area, nivel_acceso, esta fields"
```

---

## Task 2: Formulario `ConsultaForm`

**Files:**
- Modify: `usuarios/forms.py`

- [ ] **Step 1: Agregar test de form**

En `usuarios/tests/test_consulta.py`, agregar al final:

```python
from usuarios.forms import ConsultaForm


class ConsultaFormTest(TestCase):
    def test_form_valid(self):
        form = ConsultaForm(data={
            'area': 'sistemas',
            'nivel_acceso': 'basico',
            'esta': 'activo',
        })
        self.assertTrue(form.is_valid())

    def test_form_invalid_missing_area(self):
        form = ConsultaForm(data={'nivel_acceso': 'basico', 'esta': 'activo'})
        self.assertFalse(form.is_valid())
        self.assertIn('area', form.errors)
```

- [ ] **Step 2: Ejecutar test — debe fallar**

```bash
python manage.py test usuarios.tests.test_consulta.ConsultaFormTest -v 2
```
Esperado: `ImportError: cannot import name 'ConsultaForm'`

- [ ] **Step 3: Agregar `ConsultaForm` en `usuarios/forms.py`**

Al inicio del archivo, agregar `T_consulta` al import de commons.models:
```python
from commons.models import (..., T_consulta)
```

Al final del archivo, agregar:
```python
class ConsultaForm(forms.ModelForm):
    class Meta:
        model = T_consulta
        fields = ['area', 'nivel_acceso', 'esta']
        widgets = {
            'area':         forms.Select(attrs={'class': 'form-select'}),
            'nivel_acceso': forms.Select(attrs={'class': 'form-select'}),
            'esta':         forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'area':         'Área',
            'nivel_acceso': 'Nivel de acceso',
            'esta':         'Estado',
        }
```

- [ ] **Step 4: Ejecutar test — debe pasar**

```bash
python manage.py test usuarios.tests.test_consulta.ConsultaFormTest -v 2
```
Esperado: `OK (2 tests)`

- [ ] **Step 5: Commit**

```bash
git add usuarios/forms.py usuarios/tests/test_consulta.py
git commit -m "feat: add ConsultaForm for T_consulta model"
```

---

## Task 3: Permisos y dashboard

**Files:**
- Modify: `commons/management/commands/poblar_permisos.py`
- Modify: `usuarios/views.py` — función `dashboard_admin` (línea 246)

- [ ] **Step 1: Agregar `consultas` a permisos del rol `admin` en `poblar_permisos.py`**

En el dict `PERMISOS_ROL`, key `"admin"`, agregar al final de la lista (antes del cierre `]`):
```python
        ("consultas", "ver"),
        ("consultas", "editar"),
```

- [ ] **Step 2: Agregar card en `dashboard_admin` en `usuarios/views.py`**

Dentro del grupo `"Usuarios y roles"` (línea ~260), agregar al final de su lista `"items"`:
```python
                {"perm": "consultas", "url": "consultas", "img": "images/usuario.webp",
                    "titulo": "Usuarios de Consulta", "desc": "Administrar los usuarios de consulta del sistema."},
```

- [ ] **Step 3: Verificar que el servidor arranca sin errores**

```bash
python manage.py check
```
Esperado: `System check identified no issues (0 silenced).`

- [ ] **Step 4: Commit**

```bash
git add commons/management/commands/poblar_permisos.py usuarios/views.py
git commit -m "feat: add consultas permission to admin role and dashboard card"
```

---

## Task 4: Vistas CRUD

**Files:**
- Modify: `usuarios/views.py` — importar `T_consulta` y `ConsultaForm`, agregar 5 funciones

- [ ] **Step 1: Agregar test de vistas**

En `usuarios/tests/test_consulta.py`, agregar:

```python
from django.test import TestCase, Client
from django.urls import reverse


class ConsultaViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        admin_user = User.objects.create_user(username='admin1', password='pass')
        perfil_admin = T_perfil.objects.create(
            user=admin_user, nom='Admin', apelli='Test',
            tipo_dni='CC', dni=999999999, tele='3000000000',
            dire='Calle Admin', mail='admin@test.com', gene='H',
            fecha_naci='1985-01-01', rol='admin'
        )
        from commons.models import T_admin, T_permi
        T_admin.objects.create(perfil=perfil_admin, area='sistemas', esta='activo')
        T_permi.objects.create(perfil=perfil_admin, modu='consultas', acci='ver', filtro=None)
        T_permi.objects.create(perfil=perfil_admin, modu='consultas', acci='editar', filtro=None)
        self.client.login(username='admin1', password='pass')

    def test_lista_consultas_200(self):
        response = self.client.get(reverse('consultas'))
        self.assertEqual(response.status_code, 200)

    def test_crear_consulta_post(self):
        response = self.client.post(reverse('api_crear_consulta'), {
            'nom': 'Carlos', 'apelli': 'Ruiz', 'tipo_dni': 'CC',
            'dni': '111222333', 'tele': '3101234567', 'dire': 'Cra 5',
            'mail': 'carlos@test.com', 'gene': 'H', 'fecha_naci': '1995-06-15',
            'area': 'contable', 'nivel_acceso': 'basico', 'esta': 'activo',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        import json
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
```

- [ ] **Step 2: Ejecutar test — debe fallar**

```bash
python manage.py test usuarios.tests.test_consulta.ConsultaViewsTest -v 2
```
Esperado: falla por URL `consultas` no definida aún.

- [ ] **Step 3: Agregar imports en `usuarios/views.py`**

En el bloque de imports de `commons.models` (línea ~18), agregar `T_consulta`:
```python
from commons.models import (
    T_instru, T_ficha, T_cuentas, T_gestor_insti_edu, T_apre,
    T_docu_labo, T_gestor_depa, T_gestor, T_docu, T_perfil,
    T_admin, T_lider, T_repre_legal, T_munici, T_departa,
    T_insti_edu, T_centro_forma, T_progra, T_permi,
    T_consulta,   # <-- agregar
)
```

En el import de `.forms` (línea ~40), agregar `ConsultaForm`:
```python
from .forms import (..., ConsultaForm)
```

- [ ] **Step 4: Agregar las 5 vistas en `usuarios/views.py`**

Agregar al final del archivo (o después del bloque de administradores):

```python
### CONSULTAS ###

@login_required
def consultas(request):
    consultas_qs = T_consulta.objects.select_related('perfil__user').all()
    perfil_form = PerfilForm()
    consulta_form = ConsultaForm()

    acciones = PermisosMixin().get_permission_actions_for(request, "consultas")
    can_view = acciones.get("ver", False)
    can_edit = acciones.get("editar", False)
    return render(request, 'consulta.html', {
        'consultas': consultas_qs,
        'perfil_form': perfil_form,
        'consulta_form': consulta_form,
        'can_view': can_view,
        'can_edit': can_edit,
    })


@login_required
@bloquear_si_consulta
def crear_consulta(request):
    if request.method == 'POST':
        perfil_form = PerfilForm(request.POST)
        consulta_form = ConsultaForm(request.POST)

        if perfil_form.is_valid() and consulta_form.is_valid():
            dni = perfil_form.cleaned_data.get('dni')
            email = perfil_form.cleaned_data.get('mail')

            if T_perfil.objects.filter(dni__iexact=dni).exists():
                return JsonResponse({'status': 'error', 'message': 'Ya existe un usuario con ese DNI'}, status=400)
            if T_perfil.objects.filter(mail__iexact=email).exists():
                return JsonResponse({'status': 'error', 'message': 'Ya existe un usuario con ese email'}, status=400)

            nombre = perfil_form.cleaned_data['nom']
            apellido = perfil_form.cleaned_data['apelli']
            base_username = (nombre[:3] + apellido[:3]).lower()
            username = base_username
            i = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{i}"
                i += 1

            new_user = User.objects.create_user(
                username=username,
                password=str(dni),
                email=email,
            )
            new_perfil = perfil_form.save(commit=False)
            new_perfil.user = new_user
            new_perfil.rol = 'consulta'
            new_perfil.mail = new_user.email
            new_perfil.save()

            new_consulta = consulta_form.save(commit=False)
            new_consulta.perfil = new_perfil
            new_consulta.save()

            PERMISOS_CONSULTA = [
                ("usuarios", "ver"),
                ("instructores", "ver"),
                ("aprendices", "ver"),
                ("lideres", "ver"),
                ("cuentas", "ver"),
                ("gestores", "ver"),
                ("fichas", "ver"),
                ("portafolios", "ver"),
                ("instituciones", "ver"),
                ("centros", "ver"),
                ("competencias", "ver"),
                ("raps", "ver"),
            ]
            for modu, acci in PERMISOS_CONSULTA:
                T_permi.objects.get_or_create(modu=modu, acci=acci, filtro=None, perfil=new_perfil)

            return JsonResponse({'status': 'success', 'message': 'Usuario de consulta creado con éxito.'})
        else:
            errores_dict = {**perfil_form.errors.get_json_data(), **consulta_form.errors.get_json_data()}
            errores_custom = []
            for field, errors_list in errores_dict.items():
                campo = perfil_form.fields.get(field) or consulta_form.fields.get(field)
                nombre_campo = (campo.label if campo else field.capitalize())
                for err in errors_list:
                    errores_custom.append(f"{nombre_campo}: {err['message']}")
            return JsonResponse({
                'status': 'error',
                'message': 'Errores en el formulario',
                'errors': '<br>'.join(errores_custom),
            }, status=400)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)


@login_required
@bloquear_si_consulta
def obtener_consulta(request, consulta_id):
    consulta = T_consulta.objects.filter(id=consulta_id).first()
    if consulta:
        data = {
            'consulta-nom':         consulta.perfil.nom,
            'consulta-apelli':      consulta.perfil.apelli,
            'consulta-tipo_dni':    consulta.perfil.tipo_dni,
            'consulta-dni':         consulta.perfil.dni,
            'consulta-tele':        consulta.perfil.tele,
            'consulta-dire':        consulta.perfil.dire,
            'consulta-mail':        consulta.perfil.mail,
            'consulta-gene':        consulta.perfil.gene,
            'consulta-fecha_naci':  str(consulta.perfil.fecha_naci),
            'consulta-area':        consulta.area,
            'consulta-nivel_acceso': consulta.nivel_acceso,
            'consulta-esta':        consulta.esta,
        }
        return JsonResponse(data)
    return JsonResponse({'status': 'error', 'message': 'Usuario de consulta no encontrado'}, status=404)


@login_required
@bloquear_si_consulta
def editar_consulta(request, consulta_id):
    consulta = get_object_or_404(T_consulta, pk=consulta_id)
    perfil = get_object_or_404(T_perfil, pk=consulta.perfil.id)

    if request.method == 'POST':
        form_perfil = PerfilForm(request.POST, instance=perfil)
        form_consulta = ConsultaForm(request.POST, instance=consulta)

        if form_perfil.is_valid() and form_consulta.is_valid():
            form_perfil.save()
            form_consulta.save()
            return JsonResponse({'status': 'success', 'message': 'Usuario de consulta actualizado con éxito.'})
        else:
            errors = {'perfil': form_perfil.errors, 'consulta': form_consulta.errors}
            return JsonResponse({'status': 'error', 'message': 'Error al actualizar', 'errors': errors}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)


@login_required
@bloquear_si_consulta
def eliminar_consulta(request, consulta_id):
    consulta = get_object_or_404(T_consulta, pk=consulta_id)

    if request.method == 'POST':
        perfil = consulta.perfil
        usuario = perfil.user
        consulta.delete()
        perfil.delete()
        usuario.delete()
        return JsonResponse({'status': 'success', 'message': 'Usuario de consulta eliminado correctamente.'}, status=200)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)
```

- [ ] **Step 5: Ejecutar tests — deben pasar**

```bash
python manage.py test usuarios.tests.test_consulta -v 2
```
Esperado: `OK` (todos los tests).

- [ ] **Step 6: Commit**

```bash
git add usuarios/views.py usuarios/tests/test_consulta.py
git commit -m "feat: add consultas CRUD views (list, create, get, edit, delete)"
```

---

## Task 5: URLs

**Files:**
- Modify: `IOTPMV/urls.py`

- [ ] **Step 1: Agregar las 5 rutas en `IOTPMV/urls.py`**

Después del bloque `# ROL Lideres`, agregar:

```python
# ROL Consulta
path('consultas/',                                  usuarios_views.consultas,          name='consultas'),
path('api/consulta/crear/',                         usuarios_views.crear_consulta,     name='api_crear_consulta'),
path('api/consulta/<int:consulta_id>/',             usuarios_views.obtener_consulta,   name='api_obtener_consulta'),
path('api/consulta/editar/<int:consulta_id>/',      usuarios_views.editar_consulta,    name='api_editar_consulta'),
path('api/consulta/eliminar/<int:consulta_id>/',    usuarios_views.eliminar_consulta,  name='api_eliminar_consulta'),
```

- [ ] **Step 2: Verificar check**

```bash
python manage.py check
```
Esperado: `System check identified no issues (0 silenced).`

- [ ] **Step 3: Commit**

```bash
git add IOTPMV/urls.py
git commit -m "feat: add URL routes for consultas module"
```

---

## Task 6: Template `consulta.html`

**Files:**
- Create: `usuarios/templates/consulta.html`

- [ ] **Step 1: Crear el template**

```html
{% extends 'base.html' %}
{% load static %}
{% load icons %}

{% block content %}
  {% if not can_view %}
    <div class="d-flex justify-content-center align-items-center" style="height: 60vh;">
      <div class="alert alert-danger d-flex align-items-center shadow-lg rounded-3 p-4" role="alert">
        <i class="bi bi-exclamation-triangle-fill me-3 fs-3"></i>
        <div class="fw-semibold fs-5">No tiene permisos para acceder a este contenido</div>
      </div>
    </div>
  {% else %}
    <main class="container py-5" id="contenedor">
      <section class="card card-body shadow-sm p-4">
        <div class="row">
          <div class="col-12">
            <div class="d-flex justify-content-between align-items-center pb-4">
              <h1 class="display-5">Gestión de Usuarios de Consulta</h1>
              {% if can_edit %}
                <div>
                  <a class="btn btn-primary me-2" data-toggle="tooltip" data-placement="top"
                     title="Crear usuario de consulta"
                     data-bs-toggle="modal" data-bs-target="#crearConsultaModal">
                    {% icon 'plus' %}
                  </a>
                </div>
              {% endif %}
            </div>
            <div class="table-responsive">
              <table id="tabla-consultas" class="table table-hover table-bordered align-middle">
                <thead class="table-secondary text-center">
                  <tr>
                    <th>Nombres</th>
                    <th>Apellidos</th>
                    <th>Tipo Doc.</th>
                    <th>Documento</th>
                    <th>Email</th>
                    <th>Área</th>
                    <th>Nivel de Acceso</th>
                    <th>Estado</th>
                    {% if can_edit %}<th></th>{% endif %}
                  </tr>
                </thead>
                <tbody>
                  {% for c in consultas %}
                    <tr>
                      <td>{{ c.perfil.nom }}</td>
                      <td>{{ c.perfil.apelli }}</td>
                      <td>{{ c.perfil.tipo_dni }}</td>
                      <td>{{ c.perfil.dni }}</td>
                      <td>{{ c.perfil.mail }}</td>
                      <td>{{ c.get_area_display }}</td>
                      <td>{{ c.get_nivel_acceso_display }}</td>
                      <td>{{ c.get_esta_display }}</td>
                      {% if can_edit %}
                        <td>
                          <a class="btn btn-outline-warning btn-sm mb-1 edit-btn" data-id="{{ c.id }}"
                             data-toggle="tooltip" title="Editar">
                            <i class="bi bi-pencil-square"></i>
                          </a>
                          <a class="btn btn-outline-danger btn-sm delete-btn" data-id="{{ c.id }}"
                             data-toggle="tooltip" title="Eliminar">
                            {% icon 'delete' %}
                          </a>
                        </td>
                      {% endif %}
                    </tr>
                  {% endfor %}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- Modal Crear -->
    <div class="modal fade" id="crearConsultaModal" tabindex="-1" aria-labelledby="modalCrearConsultaLabel" aria-hidden="true">
      <div class="modal-dialog modal-xl">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="modalCrearConsultaLabel">Crear Usuario de Consulta</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>
          </div>
          <div class="modal-body">
            <form id="formCrearConsulta">
              {% csrf_token %}
              <h3>Datos del Perfil</h3>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label for="{{ perfil_form.nom.id_for_label }}">{{ perfil_form.nom.label }}</label>
                  {{ perfil_form.nom }}
                </div>
                <div class="col-md-6 mb-3">
                  <label for="{{ perfil_form.apelli.id_for_label }}">{{ perfil_form.apelli.label }}</label>
                  {{ perfil_form.apelli }}
                </div>
              </div>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label for="{{ perfil_form.tipo_dni.id_for_label }}">{{ perfil_form.tipo_dni.label }}</label>
                  {{ perfil_form.tipo_dni }}
                </div>
                <div class="col-md-6 mb-3">
                  <label for="{{ perfil_form.dni.id_for_label }}">{{ perfil_form.dni.label }}</label>
                  {{ perfil_form.dni }}
                </div>
              </div>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label for="{{ perfil_form.tele.id_for_label }}">{{ perfil_form.tele.label }}</label>
                  {{ perfil_form.tele }}
                </div>
                <div class="col-md-6 mb-3">
                  <label for="{{ perfil_form.dire.id_for_label }}">{{ perfil_form.dire.label }}</label>
                  {{ perfil_form.dire }}
                </div>
              </div>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label for="{{ perfil_form.mail.id_for_label }}">{{ perfil_form.mail.label }}</label>
                  {{ perfil_form.mail }}
                </div>
                <div class="col-md-6 mb-3">
                  <label for="{{ perfil_form.gene.id_for_label }}">{{ perfil_form.gene.label }}</label>
                  {{ perfil_form.gene }}
                </div>
              </div>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label for="{{ perfil_form.fecha_naci.id_for_label }}">{{ perfil_form.fecha_naci.label }}</label>
                  {{ perfil_form.fecha_naci }}
                </div>
              </div>
              <h3 class="mt-2">Datos de Consulta</h3>
              <div class="row">
                <div class="col-md-4 mb-3">
                  <label for="{{ consulta_form.area.id_for_label }}">{{ consulta_form.area.label }}</label>
                  {{ consulta_form.area }}
                </div>
                <div class="col-md-4 mb-3">
                  <label for="{{ consulta_form.nivel_acceso.id_for_label }}">{{ consulta_form.nivel_acceso.label }}</label>
                  {{ consulta_form.nivel_acceso }}
                </div>
                <div class="col-md-4 mb-3">
                  <label for="{{ consulta_form.esta.id_for_label }}">{{ consulta_form.esta.label }}</label>
                  {{ consulta_form.esta }}
                </div>
              </div>
              <div id="errorCrearConsulta" class="text-danger mt-2"></div>
              <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                <button type="submit" id="btnCrearConsulta" class="btn btn-primary">Guardar</button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal Editar -->
    <div class="modal fade" id="editarConsultaModal" tabindex="-1" aria-labelledby="modalEditarConsultaLabel" aria-hidden="true">
      <div class="modal-dialog modal-xl">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="modalEditarConsultaLabel">Editar Usuario de Consulta</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>
          </div>
          <div class="modal-body">
            <form id="formEditarConsulta">
              {% csrf_token %}
              <h3>Datos del Perfil</h3>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label for="{{ perfil_form.nom.id_for_label }}">{{ perfil_form.nom.label }}</label>
                  {{ perfil_form.nom }}
                </div>
                <div class="col-md-6 mb-3">
                  <label for="{{ perfil_form.apelli.id_for_label }}">{{ perfil_form.apelli.label }}</label>
                  {{ perfil_form.apelli }}
                </div>
              </div>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label for="{{ perfil_form.tipo_dni.id_for_label }}">{{ perfil_form.tipo_dni.label }}</label>
                  {{ perfil_form.tipo_dni }}
                </div>
                <div class="col-md-6 mb-3">
                  <label for="{{ perfil_form.dni.id_for_label }}">{{ perfil_form.dni.label }}</label>
                  {{ perfil_form.dni }}
                </div>
              </div>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label for="{{ perfil_form.tele.id_for_label }}">{{ perfil_form.tele.label }}</label>
                  {{ perfil_form.tele }}
                </div>
                <div class="col-md-6 mb-3">
                  <label for="{{ perfil_form.dire.id_for_label }}">{{ perfil_form.dire.label }}</label>
                  {{ perfil_form.dire }}
                </div>
              </div>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label for="{{ perfil_form.mail.id_for_label }}">{{ perfil_form.mail.label }}</label>
                  {{ perfil_form.mail }}
                </div>
                <div class="col-md-6 mb-3">
                  <label for="{{ perfil_form.gene.id_for_label }}">{{ perfil_form.gene.label }}</label>
                  {{ perfil_form.gene }}
                </div>
              </div>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label for="{{ perfil_form.fecha_naci.id_for_label }}">{{ perfil_form.fecha_naci.label }}</label>
                  {{ perfil_form.fecha_naci }}
                </div>
              </div>
              <h3 class="mt-2">Datos de Consulta</h3>
              <div class="row">
                <div class="col-md-4 mb-3">
                  <label for="{{ consulta_form.area.id_for_label }}">{{ consulta_form.area.label }}</label>
                  {{ consulta_form.area }}
                </div>
                <div class="col-md-4 mb-3">
                  <label for="{{ consulta_form.nivel_acceso.id_for_label }}">{{ consulta_form.nivel_acceso.label }}</label>
                  {{ consulta_form.nivel_acceso }}
                </div>
                <div class="col-md-4 mb-3">
                  <label for="{{ consulta_form.esta.id_for_label }}">{{ consulta_form.esta.label }}</label>
                  {{ consulta_form.esta }}
                </div>
              </div>
              <div id="errorEditarConsulta" class="text-danger mt-2"></div>
              <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                <button type="submit" class="btn btn-primary">Actualizar</button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  {% endif %}
{% endblock %}

{% block scripts %}
  <script type="module" src="{% static 'js/usuarios/consulta.js' %}"></script>
{% endblock %}
```

- [ ] **Step 2: Verificar que la página carga**

Con el servidor corriendo, navegar a `/consultas/` como admin y verificar que:
- La tabla aparece sin errores 500
- El botón "Crear" abre el modal correctamente

- [ ] **Step 3: Commit**

```bash
git add usuarios/templates/consulta.html
git commit -m "feat: add consulta.html template with create/edit modals"
```

---

## Task 7: JavaScript `consulta.js`

**Files:**
- Create: `static/js/usuarios/consulta.js`

- [ ] **Step 1: Crear el archivo JS**

```javascript
import { confirmDeletion, showSpinner, hideSpinner, csrfToken, showSuccessToast, showErrorToast } from '/static/js/utils.js';

document.addEventListener('DOMContentLoaded', () => {

    const btnCrear = document.getElementById('btnCrearConsulta');
    const formCrear = document.getElementById('formCrearConsulta');
    const errorCrear = document.getElementById('errorCrearConsulta');
    const formEditar = document.getElementById('formEditarConsulta');

    // ========== Crear ==========
    btnCrear.addEventListener('click', () => {
        const formData = new FormData(formCrear);
        const originalContent = btnCrear.innerHTML;

        showSpinner(btnCrear);
        formCrear.querySelectorAll('input, select, button').forEach(el => el.disabled = true);

        fetch('/api/consulta/crear/', {
            method: 'POST',
            headers: { 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' },
            body: formData,
        })
        .then(response => {
            if (!response.ok) return response.json().then(data => { throw data; });
            return response.json();
        })
        .then(data => {
            bootstrap.Modal.getInstance(document.getElementById('crearConsultaModal')).hide();
            showSuccessToast(data.message);
            formCrear.reset();
            errorCrear.innerHTML = '';
            location.reload();
        })
        .catch(error => {
            showErrorToast(error.message || 'Ocurrió un error');
            errorCrear.innerHTML = error.errors || '';
        })
        .finally(() => {
            hideSpinner(btnCrear, originalContent);
            formCrear.querySelectorAll('input, select, button').forEach(el => el.disabled = false);
        });
    });

    // ========== Editar — cargar datos ==========
    document.addEventListener('click', (e) => {
        if (e.target.closest('.edit-btn')) {
            const btn = e.target.closest('.edit-btn');
            const consultaId = btn.dataset.id;
            const originalContent = btn.innerHTML;

            showSpinner(btn);
            formEditar.querySelectorAll('input, select, button').forEach(el => el.disabled = true);

            fetch(`/api/consulta/${consultaId}/`)
                .then(response => {
                    if (!response.ok) throw new Error('Error al obtener los datos');
                    return response.json();
                })
                .then(data => {
                    formEditar.querySelector('input[name="nom"]').value          = data['consulta-nom'];
                    formEditar.querySelector('input[name="apelli"]').value       = data['consulta-apelli'];
                    formEditar.querySelector('select[name="tipo_dni"]').value    = data['consulta-tipo_dni'];
                    formEditar.querySelector('input[name="dni"]').value          = data['consulta-dni'];
                    formEditar.querySelector('input[name="tele"]').value         = data['consulta-tele'];
                    formEditar.querySelector('input[name="dire"]').value         = data['consulta-dire'];
                    formEditar.querySelector('input[name="mail"]').value         = data['consulta-mail'];
                    formEditar.querySelector('select[name="gene"]').value        = data['consulta-gene'];
                    formEditar.querySelector('input[name="fecha_naci"]').value   = data['consulta-fecha_naci'];
                    formEditar.querySelector('select[name="area"]').value        = data['consulta-area'];
                    formEditar.querySelector('select[name="nivel_acceso"]').value = data['consulta-nivel_acceso'];
                    formEditar.querySelector('select[name="esta"]').value        = data['consulta-esta'];

                    formEditar.querySelectorAll('input, select, button').forEach(el => el.disabled = false);
                    formEditar.dataset.action = `/api/consulta/editar/${consultaId}/`;
                    new bootstrap.Modal(document.getElementById('editarConsultaModal')).show();
                })
                .catch(error => {
                    showErrorToast(error.message || 'Error al cargar datos');
                })
                .finally(() => {
                    hideSpinner(btn, originalContent);
                    formEditar.querySelectorAll('input, select, button').forEach(el => el.disabled = false);
                });
        }
    });

    // ========== Editar — guardar ==========
    formEditar.addEventListener('submit', (e) => {
        e.preventDefault();
        const formData = new FormData(formEditar);
        const url = formEditar.dataset.action;
        const submitBtn = formEditar.querySelector('button[type="submit"]');
        const originalContent = submitBtn.innerHTML;

        showSpinner(submitBtn);
        formEditar.querySelectorAll('input, select, button').forEach(el => el.disabled = true);

        fetch(url, {
            method: 'POST',
            headers: { 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' },
            body: formData,
        })
        .then(async response => {
            let data;
            try { data = await response.json(); } catch { throw { message: 'Respuesta no válida.' }; }
            if (!response.ok) throw data;
            return data;
        })
        .then(data => {
            showSuccessToast(data.message);
        })
        .catch(error => {
            showErrorToast(error?.message || 'Ocurrió un error al actualizar.');
        })
        .finally(() => {
            hideSpinner(submitBtn, originalContent);
            formEditar.querySelectorAll('input, select, button').forEach(el => el.disabled = false);
            location.reload();
        });
    });

    // ========== Eliminar ==========
    document.addEventListener('click', async (e) => {
        if (e.target.closest('.delete-btn')) {
            const btn = e.target.closest('.delete-btn');
            const consultaId = btn.dataset.id;

            const confirmed = await confirmDeletion('¿Desea eliminar este usuario de consulta?');
            if (confirmed) {
                fetch(`/api/consulta/eliminar/${consultaId}/`, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' },
                })
                .then(response => response.json())
                .then(data => { showSuccessToast(data.message); })
                .catch(error => { showErrorToast(error.message); })
                .finally(() => { location.reload(); });
            }
        }
    });

});
```

- [ ] **Step 2: Verificar flujo completo en el navegador**

Con el servidor corriendo como admin:
1. Ir a `/consultas/`
2. Crear un usuario de consulta — verificar que aparece en la tabla
3. Editar el usuario — verificar que los campos se precargan y se guardan
4. Eliminar el usuario — verificar confirmación y desaparece de la tabla
5. Iniciar sesión con el usuario creado — debe redirigir a `admin_dashboard` sin opciones de edición

- [ ] **Step 3: Commit final**

```bash
git add static/js/usuarios/consulta.js
git commit -m "feat: add consulta.js for CRUD interactions on usuarios de consulta"
```

---

## Task 8: Migrar usuarios de consulta existentes (opcional)

Si hay usuarios de consulta ya creados en la BD sin `T_consulta` asociado:

- [ ] **Step 1: Correr en shell de Django**

```python
python manage.py shell
```

```python
from commons.models import T_perfil, T_consulta

perfiles_consulta = T_perfil.objects.filter(rol='consulta')
for p in perfiles_consulta:
    if not hasattr(p, 'consulta'):
        T_consulta.objects.create(
            perfil=p,
            area='sistemas',       # ajustar manualmente si se conoce el área real
            nivel_acceso='basico',
            esta='activo',
        )
        print(f"Creado T_consulta para: {p.nom} {p.apelli}")
```

- [ ] **Step 2: Verificar en `/consultas/`** que los usuarios migrados aparecen en la tabla.
