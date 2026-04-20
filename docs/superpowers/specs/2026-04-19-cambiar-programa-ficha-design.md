---
title: Cambiar programa de formación de ficha (admin only)
date: 2026-04-19
status: approved
---

# Cambiar programa de formación de ficha

## Problema

El admin necesita poder cambiar el `progra` de una ficha desde el listado de fichas. Al hacerlo, la carpeta 4 (EVIDENCIAS DE APRENDIZAJE) de los aprendices queda desincronizada porque sus RAPs fueron generados con el programa anterior. El admin debe ver un indicador persistente por fila que le avise de esta situación.

## Alcance

- Solo visible y accionable para `perfil.rol == 'admin'`
- El botón "Cambiar programa" y el indicador de desincronización son exclusivos del admin
- No regenera automáticamente carpetas — el admin ejecuta `recrear_carpeta_4_aprendiz --id_ficha X` manualmente
- Al ejecutar `recrear_carpeta_4_aprendiz`, el flag se limpia automáticamente

---

## Componentes

### 1. Migración — campo `carpetas_desincronizadas` en T_ficha

Nueva migración agrega:
```python
carpetas_desincronizadas = models.BooleanField(default=False)
```
a `T_ficha` (tabla `t_ficha`). Default `False` para todas las fichas existentes.

---

### 2. Serializer — `FichaFiltrarSerializer`

Agregar `carpetas_desincronizadas` al `fields` de `FichaFiltrarSerializer` en `api/serializers/formacion.py`:

```python
fields = FichaSerializer.Meta.fields + [
    'grupo_id', 'esta', 'fecha_aper', 'fecha_cierre',
    'centro_nom', 'insti_nom', 'instru_nom', 'num_apre_proce',
    'progra_nom', 'progra_id', 'carpetas_desincronizadas'
]
```

También agregar `progra_id = serializers.IntegerField(source='progra.id', read_only=True)` para que el modal reciba el programa actual.

---

### 3. Serializer — `FichaEditarSerializer.update()`

Agregar manejo de `progra_id` en el método `update()` en `api/serializers/formacion.py`:

```python
def update(self, instance, validated_data):
    instance.num = validated_data.get('num', instance.num)
    instance.insti = validated_data.get('insti_id', instance.insti)
    instance.centro = validated_data.get('centro_id', instance.centro)

    progra = validated_data.get('progra_id')
    if progra and progra != instance.progra:
        instance.progra = progra
        instance.carpetas_desincronizadas = True

    fase_id = self.context['request'].data.get('fase_id')
    if fase_id:
        T_fase_ficha.objects.filter(ficha=instance, vige=1).update(fase_id=fase_id)

    instance.save()
    return instance
```

`progra_id` ya está en el `fields` del serializer como `PrimaryKeyRelatedField` — agregar el campo writable:

```python
progra_id = serializers.PrimaryKeyRelatedField(
    queryset=T_progra.objects.all(), required=False
)
```

---

### 4. Nueva acción API — `lista-programas`

En `FichasViewSet` (`api/views/formacion.py`), agregar:

```python
@action(detail=False, methods=['get'], url_path='lista-programas')
def lista_programas(self, request):
    programas = T_progra.objects.all().order_by('nom').values('id', 'nom')
    return Response(list(programas))
```

Retorna todos los programas (sin filtrar por fichas existentes). Solo el admin necesita llamarlo pero no requiere restricción de rol en el backend dado que no expone datos sensibles.

---

### 5. Comando `recrear_carpeta_4_aprendiz` — limpiar flag

En `commons/management/commands/recrear_carpeta_4_aprendiz.py`, después de procesar todos los aprendices de una ficha, limpiar el flag. Agrupar el update por ficha al final del loop:

```python
for aprendiz in aprendices:
    if not aprendiz.ficha or not aprendiz.ficha.progra:
        ...
        continue

    recrear_carpeta_evidencias(aprendiz)
    self.stdout.write(self.style.SUCCESS(f"[{aprendiz.id}] Carpeta 4 recreada correctamente"))

# Limpiar flag en todas las fichas procesadas
fichas_ids = aprendices.values_list('ficha_id', flat=True).distinct()
T_ficha.objects.filter(id__in=fichas_ids).update(carpetas_desincronizadas=False)
```

---

### 6. Template `listar_fichas.html`

**Indicador de desincronización (admin only):** En la columna "Programa" del DataTable, el JS renderiza condicionalmente un ícono de advertencia si `row.carpetas_desincronizadas && userRole === 'admin'`.

**Modal cambiar programa:** Agregar al final del template (antes de `{% endblock %}`):

```html
{% if perfil.rol == 'admin' %}
<div class="modal fade" id="modalCambiarPrograma" tabindex="-1" aria-hidden="true">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">Cambiar programa de formación</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        <p class="text-muted mb-3">
          Programa actual: <strong id="programaActualNom"></strong>
        </p>
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
```

---

### 7. JS `listar_fichas.js`

**Columna Programa** — render con indicador (admin only):
```javascript
{
  data: "progra_nom",
  title: "Programa",
  render: (data, type, row) => {
    let html = data;
    if (row.carpetas_desincronizadas && userRole === 'admin') {
      html += ` <i class="bi bi-exclamation-triangle-fill text-warning"
        data-bs-toggle="tooltip"
        title="Programa actualizado — carpeta 4 desincronizada. Ejecutar: recrear_carpeta_4_aprendiz --id_ficha ${row.id}">
      </i>`;
    }
    return html;
  }
}
```

**Botón "Cambiar programa"** — en la columna de acciones (admin only):
```javascript
if (userRole === 'admin') {
  botones += `
    <button class="btn btn-outline-warning btn-sm mb-1 btn-cambiar-programa"
      data-ficha-id="${row.id}"
      data-progra-nom="${row.progra_nom}"
      data-progra-id="${row.progra_id}"
      title="Cambiar programa"
      data-bs-toggle="tooltip"
      data-bs-placement="top">
      <i class="bi bi-mortarboard"></i>
    </button>`;
}
```

**Lógica del modal:**
- Al click en `.btn-cambiar-programa`: poblar `#programaActualNom`, cargar select desde `/api/formacion/fichas/lista-programas/` en `#contenedor-nuevo-programa`, abrir `#modalCambiarPrograma`.
- `#btnGuardarPrograma`: PATCH `/api/formacion/fichas/{id}/` con `{ progra_id: <selected> }`. Al éxito: `toastSuccess`, `table.ajax.reload()`, cerrar modal.
- Al error: `toastError` con mensaje del servidor.

---

## Dependencias actualizadas

| Archivo | Cambio |
|---------|--------|
| `commons/models.py` | Campo `carpetas_desincronizadas` en T_ficha |
| `commons/migrations/XXXX_...py` | Nueva migración |
| `api/serializers/formacion.py` | FichaFiltrarSerializer + FichaEditarSerializer |
| `api/views/formacion.py` | Action `lista-programas` |
| `commons/management/commands/recrear_carpeta_4_aprendiz.py` | Limpiar flag post-ejecución |
| `formacion/templates/listar_fichas.html` | Modal + import T_progra context |
| `static/js/formacion/listar_fichas.js` | Columna progra_nom, botón, lógica modal |
