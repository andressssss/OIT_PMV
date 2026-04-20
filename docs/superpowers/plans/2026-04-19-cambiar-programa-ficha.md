# Cambiar programa de formación de ficha — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Agregar al listado de fichas un botón (admin only) para cambiar el programa de formación, con un indicador persistente (admin only) que avisa cuando las carpetas de evidencias están desincronizadas.

**Architecture:** Flag `carpetas_desincronizadas` en T_ficha como fuente de verdad. El serializer de edición lo activa al cambiar `progra`; el comando `recrear_carpeta_4_aprendiz` lo limpia. El DataTable expone el flag; el JS lo usa para renderizar el ícono y el botón condicionalmente por `userRole`.

**Tech Stack:** Django, Django REST Framework, django-mptt, Bootstrap 5, DataTables, Vanilla JS (ES modules)

---

## File Map

| Archivo | Cambio |
|---------|--------|
| `commons/models.py:336` | Agregar campo `carpetas_desincronizadas` a T_ficha |
| `commons/migrations/0155_t_ficha_carpetas_desincronizadas.py` | Nueva migración |
| `api/serializers/formacion.py:60-68` | FichaFiltrarSerializer — agregar `progra_id`, `carpetas_desincronizadas` |
| `api/serializers/formacion.py:74-123` | FichaEditarSerializer — agregar `progra_id` writable + lógica en `update()` |
| `api/views/formacion.py` | Nueva action `lista-programas` |
| `commons/management/commands/recrear_carpeta_4_aprendiz.py:109-120` | Limpiar flag al finalizar |
| `formacion/templates/listar_fichas.html:156` | Modal cambiar programa (dentro de `{% if perfil.rol == 'admin' %}`) |
| `static/js/formacion/listar_fichas.js:83` | Columna progra_nom con indicador |
| `static/js/formacion/listar_fichas.js:101-112` | Botón cambiar programa en acciones |
| `static/js/formacion/listar_fichas.js` | Lógica modal cambiar programa |

---

### Task 1: Modelo y migración

**Files:**
- Modify: `commons/models.py:336`
- Create: `commons/migrations/0155_t_ficha_carpetas_desincronizadas.py`

- [ ] **Step 1: Agregar el campo al modelo T_ficha**

En `commons/models.py`, en la clase `T_ficha`, después de la línea `corte = models.CharField(max_length=20, null=True, blank=True)` (línea 336), agregar:

```python
carpetas_desincronizadas = models.BooleanField(default=False)
```

El bloque quedará así (líneas 333-337):
```python
    esta = models.CharField(max_length=100)
    grupo = models.ForeignKey(T_grupo, on_delete=models.CASCADE)
    vige = models.CharField(max_length=20, default="2025")
    corte = models.CharField(max_length=20, null=True, blank=True)
    carpetas_desincronizadas = models.BooleanField(default=False)
```

- [ ] **Step 2: Crear la migración**

```bash
python manage.py makemigrations commons --name t_ficha_carpetas_desincronizadas
```

Resultado esperado: `commons/migrations/0155_t_ficha_carpetas_desincronizadas.py` creado.

- [ ] **Step 3: Aplicar la migración**

```bash
python manage.py migrate commons
```

Resultado esperado: `Applying commons.0155_t_ficha_carpetas_desincronizadas... OK`

- [ ] **Step 4: Commit**

```bash
git add commons/models.py commons/migrations/0155_t_ficha_carpetas_desincronizadas.py
git commit -m "feat: add carpetas_desincronizadas flag to T_ficha"
```

---

### Task 2: Serializers

**Files:**
- Modify: `api/serializers/formacion.py:1-2` (imports)
- Modify: `api/serializers/formacion.py:60-68` (FichaFiltrarSerializer)
- Modify: `api/serializers/formacion.py:74-123` (FichaEditarSerializer)

- [ ] **Step 5: Agregar T_progra al import del serializer**

En `api/serializers/formacion.py` línea 2, agregar `T_progra` al import:

```python
from commons.models import T_raps, T_compe, T_ficha, T_fase, T_fase_ficha, T_insti_edu, T_centro_forma, T_jui_eva_actu, T_jui_eva_diff, T_porta_archi, T_progra
```

- [ ] **Step 6: Actualizar FichaFiltrarSerializer**

Reemplazar la clase `FichaFiltrarSerializer` completa (líneas 60-72) con:

```python
class FichaFiltrarSerializer(FichaSerializer):
    centro_nom = serializers.CharField(source="centro.nom")
    insti_nom = serializers.CharField(source="insti.nom")
    instru_nom = serializers.SerializerMethodField()
    progra_nom = serializers.CharField(source="progra.nom")
    progra_id = serializers.IntegerField(source="progra.id", read_only=True)
    fecha_aper = serializers.DateTimeField(format="%d/%m/%Y")

    class Meta:
        model = T_ficha
        fields = FichaSerializer.Meta.fields + [
            'grupo_id', 'esta', 'fecha_aper', 'fecha_cierre',
            'centro_nom', 'insti_nom', 'instru_nom', 'num_apre_proce',
            'progra_nom', 'progra_id', 'carpetas_desincronizadas'
        ]

    def get_instru_nom(self, value):
        return value.instru.perfil.nom if value.instru else None
```

- [ ] **Step 7: Actualizar FichaEditarSerializer — agregar progra_id writable**

En `FichaEditarSerializer`, después de la línea:
```python
    centro_id = serializers.PrimaryKeyRelatedField(
        queryset=T_centro_forma.objects.all(), required=False)
```

Agregar:
```python
    progra_id = serializers.PrimaryKeyRelatedField(
        queryset=T_progra.objects.all(), required=False, source='progra')
```

- [ ] **Step 8: Actualizar FichaEditarSerializer.update() — manejar progra y flag**

Reemplazar el método `update()` completo (líneas 112-123):

```python
    def update(self, instance, validated_data):
        instance.num = validated_data.get('num', instance.num)
        instance.insti = validated_data.get('insti_id', instance.insti)
        instance.centro = validated_data.get('centro_id', instance.centro)

        nuevo_progra = validated_data.get('progra')
        if nuevo_progra and nuevo_progra != instance.progra:
            instance.progra = nuevo_progra
            instance.carpetas_desincronizadas = True

        fase_id = self.context['request'].data.get('fase_id')
        if fase_id:
            T_fase_ficha.objects.filter(
                ficha=instance, vige=1).update(fase_id=fase_id)

        instance.save()
        return instance
```

- [ ] **Step 9: Verificar que la app inicia sin errores**

```bash
python manage.py check
```

Resultado esperado: `System check identified no issues (0 silenced).`

- [ ] **Step 10: Commit**

```bash
git add api/serializers/formacion.py
git commit -m "feat: expose progra_id and carpetas_desincronizadas in ficha serializers"
```

---

### Task 3: Endpoint lista-programas

**Files:**
- Modify: `api/views/formacion.py` (después de `opciones_programas`, ~línea 847)

- [ ] **Step 11: Agregar la action lista-programas**

En `api/views/formacion.py`, inmediatamente después del cierre del método `opciones_programas`, agregar:

```python
    @action(detail=False, methods=['get'], url_path='lista-programas')
    def lista_programas(self, request):
        programas = T_progra.objects.all().order_by('nom').values('id', 'nom')
        return Response(list(programas))
```

- [ ] **Step 12: Verificar el endpoint**

```bash
python manage.py check
```

Resultado esperado: `System check identified no issues (0 silenced).`

- [ ] **Step 13: Commit**

```bash
git add api/views/formacion.py
git commit -m "feat: add lista-programas endpoint to FichasViewSet"
```

---

### Task 4: Limpiar flag en recrear_carpeta_4_aprendiz

**Files:**
- Modify: `commons/management/commands/recrear_carpeta_4_aprendiz.py:2` (import)
- Modify: `commons/management/commands/recrear_carpeta_4_aprendiz.py:109-120` (handle loop)

- [ ] **Step 14: Agregar T_ficha al import del comando**

En `commons/management/commands/recrear_carpeta_4_aprendiz.py` línea 2:

```python
from commons.models import T_apre, T_DocumentFolderAprendiz, T_fase, T_raps, T_ficha
```

- [ ] **Step 15: Limpiar el flag después del loop de aprendices**

Reemplazar el método `handle()` completo (líneas 88-120):

```python
    def handle(self, *args, **options):
        id_aprendiz = options.get("id_aprendiz")
        id_ficha = options.get("id_ficha")
        if id_aprendiz:
            aprendices = T_apre.objects.filter(id=id_aprendiz)
            if not aprendices.exists():
                self.stdout.write(self.style.ERROR(
                    f"No se encontró el aprendiz con id={id_aprendiz}"
                ))
                return
        elif id_ficha:
            aprendices = T_apre.objects.filter(ficha__id=id_ficha)
            if not aprendices.exists():
                self.stdout.write(self.style.ERROR(
                    f"No se encontraron aprendices relacionados a la ficha={id_ficha}"
                ))
                return
        else:
            self.stdout.write("Por seguridad esta función requiere objetivar la muestra de aprendices, use algún parámetro")
            return

        for aprendiz in aprendices:
            if not aprendiz.ficha or not aprendiz.ficha.progra:
                self.stdout.write(
                    f"[{aprendiz.id}] No tiene ficha o programa asociado, se omite"
                )
                continue

            recrear_carpeta_evidencias(aprendiz)

            self.stdout.write(self.style.SUCCESS(
                f"[{aprendiz.id}] Carpeta 4 recreada correctamente"
            ))

        fichas_ids = aprendices.values_list('ficha_id', flat=True).distinct()
        T_ficha.objects.filter(id__in=fichas_ids).update(carpetas_desincronizadas=False)
        self.stdout.write(self.style.SUCCESS("Flag carpetas_desincronizadas limpiado."))
```

- [ ] **Step 16: Commit**

```bash
git add commons/management/commands/recrear_carpeta_4_aprendiz.py
git commit -m "feat: clear carpetas_desincronizadas flag after recrear_carpeta_4"
```

---

### Task 5: Template — modal cambiar programa

**Files:**
- Modify: `formacion/templates/listar_fichas.html:154-156` (antes de `{% endif %}{% endblock %}`)

- [ ] **Step 17: Agregar el modal dentro del bloque admin**

La estructura actual del final de `formacion/templates/listar_fichas.html` es:
```html
    <!-- Modal: Asignar aprendices -->
    <div class="modal fade" id="modalAsignarAprendices" ...>
      ...
    </div>
  {% endif %}   ← cierra {% if perfil.rol == 'admin' %}
{% endblock %}
```

Insertar el nuevo modal ANTES de `{% endif %}` (antes del cierre del bloque admin). Reemplazar:

```html
    </div>
  {% endif %}
{% endblock %}
```

Por:

```html
    </div>

    <!-- Modal: Cambiar programa de formación -->
    <div class="modal fade" id="modalCambiarPrograma" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Cambiar programa de formación</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>
          </div>
          <div class="modal-body">
            <p class="text-muted mb-3">Programa actual: <strong id="programaActualNom"></strong></p>
            <div id="contenedor-nuevo-programa"></div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
            <button type="button" class="btn btn-primary" id="btnGuardarPrograma">Guardar</button>
          </div>
        </div>
      </div>
    </div>
  {% endif %}
{% endblock %}
```

El modal hereda la restricción admin del `{% if perfil.rol == 'admin' %}` que lo envuelve — no necesita su propio `{% if %}`.

- [ ] **Step 18: Commit**

```bash
git add formacion/templates/listar_fichas.html
git commit -m "feat: add cambiar programa modal to listar_fichas template"
```

---

### Task 6: JS — indicador, botón y lógica del modal

**Files:**
- Modify: `static/js/formacion/listar_fichas.js:83` (columna progra_nom)
- Modify: `static/js/formacion/listar_fichas.js:101-112` (columna acciones)
- Modify: `static/js/formacion/listar_fichas.js` (lógica modal, al final del DOMContentLoaded)

- [ ] **Step 19: Actualizar columna progra_nom con indicador admin**

En `static/js/formacion/listar_fichas.js`, reemplazar la línea:
```javascript
          { data: "progra_nom", title: "Programa" },
```
Por:
```javascript
          {
            data: "progra_nom",
            title: "Programa",
            render: (data, type, row) => {
              let html = data || "No registrado";
              if (row.carpetas_desincronizadas && userRole === "admin") {
                html += ` <i class="bi bi-exclamation-triangle-fill text-warning"
                  data-bs-toggle="tooltip"
                  data-bs-placement="top"
                  title="Programa actualizado — carpeta 4 desincronizada. Ejecutar: python manage.py recrear_carpeta_4_aprendiz --id_ficha ${row.id}">
                </i>`;
              }
              return html;
            },
          },
```

- [ ] **Step 20: Agregar botón cambiar programa en la columna de acciones**

En `static/js/formacion/listar_fichas.js`, reemplazar el bloque de la columna de acciones (dentro del `render` de `data: null`):

```javascript
          {
            data: null,
            orderable: false,
            render: function (data, type, row) {
              let botones = "";

              if (data.can_view_p) {
                botones += `
              <a class="btn btn-outline-primary btn-sm mb-1" 
                  href="/ficha/${row.id}/"
                  title="Ver ficha"
                  data-bs-toggle="tooltip" 
                  data-bs-placement="top">
                  <i class="bi bi-journals"></i>
              </a>
            `;
              }
              if (data.can_edit) {
                botones += `
              <a class="btn btn-outline-warning btn-sm mb-1 btnEditarFicha"
                  data-id="${row.id}"
                  title="Editar ficha"
                  data-bs-toggle="tooltip" 
                  data-bs-placement="top">
                  <i class="bi bi-pencil-square"></i>
              </a>
            `;
              }
              if (userRole === "admin") {
                botones += `
              <button class="btn btn-outline-secondary btn-sm mb-1 btn-cambiar-programa"
                  data-ficha-id="${row.id}"
                  data-progra-nom="${row.progra_nom}"
                  data-progra-id="${row.progra_id}"
                  title="Cambiar programa de formación"
                  data-bs-toggle="tooltip"
                  data-bs-placement="top">
                  <i class="bi bi-mortarboard"></i>
              </button>
            `;
              }
              return botones;
            },
          },
```

- [ ] **Step 21: Agregar lógica del modal cambiar programa**

En `static/js/formacion/listar_fichas.js`, justo antes del cierre del `document.addEventListener("DOMContentLoaded", () => {` (antes de la última `}`), agregar:

```javascript
  // ── Cambiar programa de formación ──────────────────────────────────────
  const modalCambiarProgramaEl = document.getElementById("modalCambiarPrograma");

  if (modalCambiarProgramaEl) {
    let fichaIdSeleccionada = null;

    tableEl.addEventListener("click", async (e) => {
      const btn = e.target.closest(".btn-cambiar-programa");
      if (!btn) return;

      fichaIdSeleccionada = btn.dataset.fichaId;
      document.getElementById("programaActualNom").textContent = btn.dataset.programaNom;

      const contenedor = document.getElementById("contenedor-nuevo-programa");
      contenedor.innerHTML = `<div class="placeholder-glow"><span class="placeholder col-12 rounded"></span></div>`;

      const modalInstance = new bootstrap.Modal(modalCambiarProgramaEl);
      modalInstance.show();

      try {
        const res = await fetch("/api/formacion/fichas/lista-programas/");
        const programas = await res.json();

        const select = document.createElement("select");
        select.id = "nuevo-programa";
        select.className = "form-select";
        select.innerHTML = `<option value="">Seleccione un programa</option>` +
          programas.map((p) => `<option value="${p.id}">${p.nom}</option>`).join("");

        contenedor.innerHTML = "";
        contenedor.appendChild(select);
      } catch (err) {
        toastError("Error al cargar programas");
      }
    });

    document.getElementById("btnGuardarPrograma").addEventListener("click", async () => {
      const select = document.getElementById("nuevo-programa");
      if (!select || !select.value) {
        toastWarning("Seleccione un programa");
        return;
      }

      const btn = document.getElementById("btnGuardarPrograma");
      const originalContent = btn.innerHTML;
      showSpinner(btn);

      try {
        const res = await fetch(`/api/formacion/fichas/${fichaIdSeleccionada}/`, {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
            "X-Requested-With": "XMLHttpRequest",
          },
          body: JSON.stringify({ progra_id: parseInt(select.value) }),
        });

        const data = await res.json();

        if (!res.ok) {
          const mensaje = data.message || data.detail || Object.values(data).flat().join(", ");
          toastError(mensaje);
          return;
        }

        toastSuccess("Programa actualizado correctamente");
        bootstrap.Modal.getInstance(modalCambiarProgramaEl).hide();
        table.ajax.reload(null, false);
      } catch (err) {
        toastError("Error al actualizar el programa");
      } finally {
        hideSpinner(btn, originalContent);
      }
    });
  }
```

- [ ] **Step 22: Commit**

```bash
git add static/js/formacion/listar_fichas.js formacion/templates/listar_fichas.html
git commit -m "feat: add cambiar programa button, warning indicator, and modal logic"
```
