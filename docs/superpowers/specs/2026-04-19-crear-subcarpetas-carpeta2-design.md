---
title: Crear subcarpetas faltantes en carpeta 2 - Mantenimiento
date: 2026-04-19
status: approved
---

# Crear subcarpetas faltantes en carpeta "2. PLANEACION SEGUIMIENTO Y EVALUACION ETAPA PRODUCTIVA"

## Problema

Algunos aprendices existentes tienen la carpeta raíz "2. PLANEACION SEGUIMIENTO Y EVALUACION ETAPA PRODUCTIVA" pero sin las subcarpetas que deben contener. Esto ocurrió porque en `actualizar_estructura_aprendices.py` la carpeta 2 está definida sin hijos (`{}`).

## Alcance

Solo corrige aprendices existentes. No modifica `actualizar_estructura_aprendices.py`.

## Solución

Nuevo management command Django: `commons/management/commands/crear_subcarpetas_carpeta2.py`

### Subcarpetas a crear

```
EVIDENCIAS PROYECTO PRODUCTIVO
GFPI-F-023-PLANEACIÓN, SEGUIMIENTO Y EVALUACIÓN ETAPA PRODUCTIVA
GFPI-F-147-BITÁCORAS SEGUIMIENTO ETAPA PRODUCTIVA
GFPI-F-165-V4-INSCRIPCIÓN A ETAPA PRODUCTIVA
PROCESO DE CERTIFICACIÓN
```

### Argumentos

| Argumento | Descripción |
|-----------|-------------|
| `--dry-run` | Solo reporta las carpetas afectadas y sus fichas, sin escribir en BD |
| `--id_aprendiz` | Limita la ejecución a un aprendiz específico (para pruebas) |

### Lógica

1. Consulta todas las `T_DocumentFolderAprendiz` con `name="2. PLANEACION SEGUIMIENTO Y EVALUACION ETAPA PRODUCTIVA"`.
2. Filtra las que no tienen hijos usando `.get_children().exists()` (MPTT).
3. **Con `--dry-run`:** imprime tabla `id_carpeta | aprendiz_id | ficha | nombre` + conteo total. Sin writes.
4. **Sin `--dry-run`:** crea las 5 subcarpetas con `get_or_create` para cada carpeta afectada. Imprime cuántas se crearon vs ya existían.

### Inserción

```python
T_DocumentFolderAprendiz.objects.get_or_create(
    name=nombre_subcarpeta,
    tipo="carpeta",
    aprendiz=carpeta.aprendiz,
    parent=carpeta
)
```

El ORM MPTT recalcula `lft`, `rght`, `tree_id`, `level` automáticamente.

### Ejecución

```bash
# Ver qué fichas serían afectadas
python manage.py crear_subcarpetas_carpeta2 --dry-run

# Ejecutar para un aprendiz de prueba
python manage.py crear_subcarpetas_carpeta2 --id_aprendiz 123

# Ejecutar para todos los aprendices afectados
python manage.py crear_subcarpetas_carpeta2
```

## Idempotencia

El uso de `get_or_create` garantiza que correr el comando múltiples veces no genera duplicados.
