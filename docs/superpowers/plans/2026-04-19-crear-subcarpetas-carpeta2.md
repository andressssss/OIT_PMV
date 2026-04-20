# Crear subcarpetas faltantes carpeta 2 - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Crear un management command Django que inyecte las 5 subcarpetas faltantes en la carpeta "2. PLANEACION SEGUIMIENTO Y EVALUACION ETAPA PRODUCTIVA" de los aprendices que no las tienen.

**Architecture:** Un solo management command idempotente que usa `get_or_create` para cada subcarpeta. Detecta carpetas sin hijos con MPTT. Soporta `--dry-run` para reportar afectados sin escribir y `--id_aprendiz` para pruebas puntuales.

**Tech Stack:** Django management commands, django-mptt (`T_DocumentFolderAprendiz`), `commons.models`

---

### Task 1: Crear el management command

**Files:**
- Create: `commons/management/commands/crear_subcarpetas_carpeta2.py`

- [ ] **Step 1: Crear el archivo del comando**

Crea `commons/management/commands/crear_subcarpetas_carpeta2.py` con el siguiente contenido completo:

```python
from django.core.management.base import BaseCommand
from commons.models import T_apre, T_DocumentFolderAprendiz

NOMBRE_CARPETA_2 = "2. PLANEACION SEGUIMIENTO Y EVALUACION ETAPA PRODUCTIVA"

SUBCARPETAS = [
    "EVIDENCIAS PROYECTO PRODUCTIVO",
    "GFPI-F-023-PLANEACIÓN, SEGUIMIENTO Y EVALUACIÓN ETAPA PRODUCTIVA",
    "GFPI-F-147-BITÁCORAS SEGUIMIENTO ETAPA PRODUCTIVA",
    "GFPI-F-165-V4-INSCRIPCIÓN A ETAPA PRODUCTIVA",
    "PROCESO DE CERTIFICACIÓN",
]


def get_carpetas_sin_hijos(id_aprendiz=None):
    """Retorna las carpetas 2 que no tienen subcarpetas."""
    qs = T_DocumentFolderAprendiz.objects.filter(
        name=NOMBRE_CARPETA_2,
        tipo="carpeta",
    ).select_related("aprendiz__ficha")

    if id_aprendiz:
        qs = qs.filter(aprendiz__id=id_aprendiz)

    return [c for c in qs if not c.get_children().exists()]


class Command(BaseCommand):
    help = "Crea las subcarpetas faltantes en la carpeta 2 de aprendices existentes"

    def add_arguments(self, parser):
        parser.add_argument(
            "--id_aprendiz",
            type=int,
            help="ID de un aprendiz específico para procesar",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Solo muestra qué carpetas serían afectadas, sin escribir en BD",
        )

    def handle(self, *args, **options):
        id_aprendiz = options.get("id_aprendiz")
        dry_run = options.get("dry_run")

        carpetas = get_carpetas_sin_hijos(id_aprendiz)

        if not carpetas:
            self.stdout.write(self.style.SUCCESS("No hay carpetas afectadas."))
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"DRY RUN — {len(carpetas)} carpeta(s) serían afectadas:\n"
                )
            )
            self.stdout.write(
                f"{'ID carpeta':<12} {'Aprendiz ID':<14} {'Ficha':<12} Nombre carpeta"
            )
            self.stdout.write("-" * 70)
            for c in carpetas:
                ficha_num = c.aprendiz.ficha.num if c.aprendiz.ficha else "Sin ficha"
                self.stdout.write(
                    f"{c.id:<12} {c.aprendiz.id:<14} {ficha_num:<12} {c.name}"
                )
            self.stdout.write(
                f"\nSubcarpetas que se crearían por carpeta: {len(SUBCARPETAS)}"
            )
            self.stdout.write(
                f"Total subcarpetas a crear: {len(carpetas) * len(SUBCARPETAS)}"
            )
            return

        creadas_total = 0
        existentes_total = 0

        for carpeta in carpetas:
            for nombre in SUBCARPETAS:
                _, created = T_DocumentFolderAprendiz.objects.get_or_create(
                    name=nombre,
                    tipo="carpeta",
                    aprendiz=carpeta.aprendiz,
                    parent=carpeta,
                )
                if created:
                    creadas_total += 1
                else:
                    existentes_total += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"[aprendiz {carpeta.aprendiz.id}] Subcarpetas procesadas."
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nListo. Creadas: {creadas_total} | Ya existían: {existentes_total}"
            )
        )
```

- [ ] **Step 2: Verificar que el archivo existe**

```bash
ls commons/management/commands/crear_subcarpetas_carpeta2.py
```

Resultado esperado: el archivo listado sin error.

- [ ] **Step 3: Verificar que Django reconoce el comando**

```bash
python manage.py crear_subcarpetas_carpeta2 --help
```

Resultado esperado: muestra el help con los argumentos `--id_aprendiz` y `--dry-run`.

---

### Task 2: Validar con dry-run

- [ ] **Step 4: Ejecutar dry-run general**

```bash
python manage.py crear_subcarpetas_carpeta2 --dry-run
```

Resultado esperado: tabla con columnas `ID carpeta | Aprendiz ID | Ficha | Nombre carpeta` y conteo de subcarpetas a crear. Sin ningún cambio en BD.

- [ ] **Step 5: Ejecutar dry-run para un aprendiz específico (prueba puntual)**

Toma un `ID` de aprendiz de la lista que mostró el dry-run anterior y ejecuta:

```bash
python manage.py crear_subcarpetas_carpeta2 --dry-run --id_aprendiz <ID>
```

Resultado esperado: solo aparece ese aprendiz en el reporte.

---

### Task 3: Ejecutar en un aprendiz de prueba y verificar en BD

- [ ] **Step 6: Crear subcarpetas para un aprendiz de prueba**

```bash
python manage.py crear_subcarpetas_carpeta2 --id_aprendiz <ID>
```

Resultado esperado:
```
[aprendiz <ID>] Subcarpetas procesadas.

Listo. Creadas: 5 | Ya existían: 0
```

- [ ] **Step 7: Verificar en BD que las 5 subcarpetas existen**

Ejecuta esta consulta SQL (o en el shell de Django) para confirmar:

```sql
SELECT id, name, parent_id
FROM commons_t_documentfolderaprendiz
WHERE parent_id = (
    SELECT id FROM commons_t_documentfolderaprendiz
    WHERE name = '2. PLANEACION SEGUIMIENTO Y EVALUACION ETAPA PRODUCTIVA'
      AND aprendiz_id = <ID>
)
ORDER BY name;
```

Resultado esperado: 5 filas con los nombres exactos de SUBCARPETAS.

- [ ] **Step 8: Verificar idempotencia — correr de nuevo para el mismo aprendiz**

```bash
python manage.py crear_subcarpetas_carpeta2 --id_aprendiz <ID>
```

Resultado esperado:
```
[aprendiz <ID>] Subcarpetas procesadas.

Listo. Creadas: 0 | Ya existían: 5
```

---

### Task 4: Ejecutar para todos los aprendices afectados y hacer commit

- [ ] **Step 9: Ejecutar para todos los aprendices afectados**

```bash
python manage.py crear_subcarpetas_carpeta2
```

Resultado esperado: una línea de éxito por cada aprendiz procesado y un resumen final con totales.

- [ ] **Step 10: Hacer commit del nuevo comando**

```bash
git add commons/management/commands/crear_subcarpetas_carpeta2.py docs/superpowers/specs/2026-04-19-crear-subcarpetas-carpeta2-design.md docs/superpowers/plans/2026-04-19-crear-subcarpetas-carpeta2.md
git commit -m "feat: add management command to create missing subfolders in carpeta 2"
```
