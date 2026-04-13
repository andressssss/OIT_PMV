# Modulo de Administracion de Plantillas de Estructura Documental (Fichas)

## Resumen

Reemplazar las estructuras de carpetas hardcodeadas en scripts Python por un modulo de administracion con UI que permita editar la plantilla de estructura documental de fichas, controlar visibilidad y permisos por rol, versionar cambios, y aplicarlos de forma controlada a fichas existentes o nuevas. Solo para fichas en este alcance.

## Contexto

### Estado actual

- La estructura documental de fichas esta definida como un diccionario Python en `commons/management/commands/actualizar_estructura_fichas.py`.
- Cada cambio requiere modificar codigo, hacer deploy, y ejecutar un management command.
- Ajustes puntuales se han hecho con scripts ad-hoc que contienen listas de IDs de fichas hardcodeados (ej: `actualizar_portafolio_a_2.py` con +1200 IDs).
- No hay trazabilidad de quien pidio un cambio, cuando se aplico, ni a que fichas afecto.
- No existe mecanismo para ocultar carpetas por rol ni controlar permisos de edicion por carpeta.
- En produccion existen +1000 fichas con documentacion.

### Problemas que resuelve

1. Agregar/renombrar/ocultar carpetas sin deploy ni scripts
2. Visibilidad y permisos de edicion por rol y por carpeta
3. Trazabilidad completa de cambios y aplicaciones
4. Aplicacion controlada a subconjuntos de fichas (por corte, por listado, todas, solo nuevas)
5. Historial de versiones con posibilidad de revertir

## Alcance

- Solo fichas (`T_DocumentFolder`). Aprendices (`T_DocumentFolderAprendiz`) queda para una fase futura.
- La estructura de fichas es 100% estatica (no tiene carpetas dinamicas por RAPs/competencias como aprendices).
- El portafolio que ven los usuarios sigue con el JS manual actual (`panel_ficha.js`). No se migra a Wunderbaum.
- El editor de plantillas (solo admin) usa Wunderbaum con edicion habilitada.

## Modelos de datos

### T_PlantillaNodo (MPTTModel)

Arbol que representa la estructura modelo de carpetas para fichas.

| Campo | Tipo | Descripcion |
|---|---|---|
| `name` | CharField(255) | Nombre de la carpeta |
| `parent` | TreeForeignKey(self, null, blank) | Nodo padre (MPTT) |
| `orden` | IntegerField(default=0) | Orden entre hermanos (0-indexed) |
| `roles_visibles` | JSONField(null=True) | Roles que ven la carpeta. Null = todos |
| `roles_editables` | JSONField(null=True) | Roles que pueden subir/eliminar docs. Null = todos |
| `activo` | BooleanField(default=True) | False = oculto (nunca se elimina) |
| `fecha_crea` | DateTimeField(auto_now_add) | Fecha de creacion |
| `usuario_crea` | FK(User) | Quien creo el nodo |

db_table: `t_plantilla_nodo`

### T_PlantillaVersion

Historial de versiones de la plantilla.

| Campo | Tipo | Descripcion |
|---|---|---|
| `version` | IntegerField | Numero autoincremental |
| `snapshot` | JSONField | Foto completa del arbol al momento de guardar |
| `descripcion` | CharField(500) | Descripcion del cambio |
| `fecha` | DateTimeField(auto_now_add) | Fecha |
| `usuario` | FK(User) | Quien guardo la version |

db_table: `t_plantilla_version`

### T_PlantillaAplicacion

Registro de cada aplicacion de plantilla a fichas.

| Campo | Tipo | Descripcion |
|---|---|---|
| `version` | FK(T_PlantillaVersion) | Version aplicada |
| `ficha` | FK(T_ficha) | Ficha destino |
| `resultado` | CharField(50) | "exitoso", "parcial", "error" |
| `detalle` | JSONField | Nodos agregados, nodos ocultados |
| `fecha` | DateTimeField(auto_now_add) | Fecha |
| `usuario` | FK(User) | Quien ejecuto |

db_table: `t_plantilla_aplicacion`

### T_PlantillaAdmin

Lista blanca de usuarios autorizados a usar el modulo.

| Campo | Tipo | Descripcion |
|---|---|---|
| `user` | OneToOneField(User) | Usuario autorizado |

db_table: `t_plantilla_admin`

### Campos nuevos en T_DocumentFolder

| Campo | Tipo | Default | Descripcion |
|---|---|---|---|
| `oculto` | BooleanField | False | Si True, no se muestra en el portafolio |
| `roles_visibles` | JSONField | null | Roles que ven la carpeta. Null = todos |
| `roles_editables` | JSONField | null | Roles que pueden editar. Null = todos |

### Campo nuevo en T_ficha

| Campo | Tipo | Default | Descripcion |
|---|---|---|---|
| `corte` | CharField(20, null, blank) | null | Identificador del corte semestral. Ej: "2026-1" |

## Logica de aplicacion a fichas

### Algoritmo de reconciliacion (solo aditivo/ocultivo)

Para cada ficha seleccionada:

1. Recorrer el arbol de `T_PlantillaNodo` en orden MPTT.
2. Para cada nodo de la plantilla:
   - Buscar en `T_DocumentFolder` de la ficha un nodo con el mismo `name` y mismo padre equivalente.
   - Si **NO existe** y `activo=True` en plantilla: crear el nodo en `T_DocumentFolder`.
   - Si **EXISTE** y `activo=False` en plantilla: marcar `oculto=True` en `T_DocumentFolder`.
   - Si **EXISTE** y `activo=True`: sincronizar `roles_visibles` y `roles_editables`.
   - **NUNCA eliminar** nodos existentes en `T_DocumentFolder`.
3. Registrar en `T_PlantillaAplicacion` con detalle de operaciones realizadas.

### Modos de seleccion de fichas

- **Todas**: aplica a todas las fichas en la BD.
- **Por corte**: selecciona fichas donde `T_ficha.corte` coincida con el valor elegido.
- **Por listado**: textarea con numeros de ficha separados por coma/salto de linea.
- **Solo fichas nuevas**: flag en la version que marca "aplicar automaticamente a fichas nuevas al crearlas".

### Impacto en fichas existentes

Los defaults de los campos nuevos (`oculto=False`, `roles_visibles=null`, `roles_editables=null`) garantizan que fichas que nunca se toquen desde el modulo siguen funcionando exactamente igual.

## Cambios en el portafolio existente

### Vista `obtener_carpetas`

Se modifica para respetar los campos nuevos:

- Excluir nodos con `oculto=True`.
- Excluir nodos donde el rol del usuario no este en `roles_visibles` (si no es null).
- Incluir flag `can_edit_folder` por nodo: False si el rol no esta en `roles_editables`.

### Frontend `panel_ficha.js`

- `renderTree()` recibe `can_edit_folder` por nodo y condiciona la aparicion del boton "Cargar documento" y el icono de eliminar.
- No se cambia la tecnologia de renderizado (sigue JS manual).

## UI del modulo admin

### Acceso

- Nueva entrada en el menu lateral, visible solo para usuarios en `T_PlantillaAdmin`.
- Ruta base: `/plantillas/`.
- Validacion en backend: si el usuario no esta en `T_PlantillaAdmin`, retorna 403.

### Editor de arbol (`/plantillas/editor/`)

- Arbol renderizado con Wunderbaum en modo editable.
- Acciones por nodo:
  - **Agregar hijo**: crea nodo nuevo dentro del seleccionado.
  - **Renombrar**: edicion inline del nombre.
  - **Mover**: drag & drop para reordenar o reubicar.
  - **Ocultar/Mostrar**: toggle de `activo` (nodo se atenua visualmente).
  - **Configurar visibilidad**: modal con checkboxes por rol (quien ve, quien edita).
- Boton "Guardar version": pide descripcion del cambio, crea snapshot en `T_PlantillaVersion`.

### Historial (`/plantillas/historial/`)

- Tabla con versiones: numero, descripcion, usuario, fecha.
- Accion "Ver": muestra el arbol de esa version en modo solo lectura.
- Accion "Restaurar": carga esa version como la vigente (crea version nueva basada en la anterior).

### Aplicacion (`/plantillas/aplicar/`)

- Seleccion de version a aplicar (default: la vigente).
- Seleccion de fichas destino: todas, por corte, por listado, solo nuevas.
- Boton "Vista previa": muestra cuantas fichas serian afectadas y que cambios se harian.
- Boton "Aplicar": ejecuta la reconciliacion y muestra resumen con resultados.

### Log de aplicaciones (`/plantillas/log/`)

- Tabla con aplicaciones realizadas: version, fichas, resultado, usuario, fecha.
- Filtrable por corte, fecha, usuario.

## Migracion y transicion

### Paso 1 — Migraciones de BD

- Crear modelos nuevos: `T_PlantillaNodo`, `T_PlantillaVersion`, `T_PlantillaAplicacion`, `T_PlantillaAdmin`.
- Agregar campos a `T_DocumentFolder`: `oculto`, `roles_visibles`, `roles_editables`.
- Agregar campo `corte` a `T_ficha`.

### Paso 2 — Data migration

- Cargar el diccionario `estructura_documental` de `actualizar_estructura_fichas.py` como nodos en `T_PlantillaNodo`.
- Crear `T_PlantillaVersion` v1 con snapshot y descripcion "Estructura inicial migrada desde codigo".

### Paso 3 — Filtro de visibilidad en portafolio

- Modificar `obtener_carpetas` para respetar `oculto`, `roles_visibles`, `roles_editables`.
- Modificar `renderTree()` para respetar `can_edit_folder` por nodo.

### Paso 4 — Panel admin

- Implementar las vistas del editor, historial, aplicacion y log.

### Paso 5 — Integracion con creacion de fichas

- Cuando se crea una ficha nueva, si hay una version marcada como "aplicar a fichas nuevas", se ejecuta la reconciliacion automaticamente.

### Paso 6 — Carga de cortes

- Se carga el campo `corte` de fichas existentes con los datos proporcionados.

### Deprecacion de scripts

Los management commands existentes (`actualizar_estructura_fichas.py`, etc.) permanecen como fallback pero dejan de ser el mecanismo principal. La creacion de fichas nuevas pasa a usar la plantilla vigente.

## Decisiones de diseno

| Decision | Eleccion | Razon |
|---|---|---|
| Almacenamiento de plantilla | Arbol MPTT en BD | Consistente con T_DocumentFolder, queries eficientes por nodo |
| Versionamiento | Snapshot JSON completo por version | Permite comparar y restaurar versiones completas |
| Aplicacion de cambios | Solo aditiva/ocultiva | Los documentos son lo mas importante, nunca se pierden |
| Tecnologia del editor | Wunderbaum | Drag & drop y edicion inline nativos, ya es dependencia del proyecto |
| Tecnologia del portafolio | JS manual existente | Funciona, esta probado, no se toca |
| Control de acceso | Lista blanca por usuario (T_PlantillaAdmin) | Granularidad maxima, no depende solo del rol |
| Seleccion de fichas | Todas / por corte / por listado / solo nuevas | Cubre todos los escenarios operativos actuales |

## Fuera de alcance

- Plantillas para aprendices (`T_DocumentFolderAprendiz`) — fase futura.
- Carpetas dinamicas por RAPs/competencias — solo aplica a aprendices.
- Migracion del portafolio a Wunderbaum — el JS manual actual no se toca.
