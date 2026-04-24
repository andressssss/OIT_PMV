# Módulo de Administración de Usuarios de Consulta

**Fecha:** 2026-04-21  
**Estado:** Aprobado  
**Enfoque:** Opción A — Seguir el patrón exacto del codebase

---

## Contexto

El rol `consulta` ya existe en `ROL_CHOICES` de `T_perfil` y cuenta con permisos predefinidos de solo lectura en `poblar_permisos.py`. Sin embargo, a diferencia de todos los demás roles (`admin`, `instructor`, `lider`, `gestor`), no tiene modelo propio ni sección de administración. Hasta ahora se crean manualmente en la BD o como admins.

---

## Modelo — `T_consulta`

**Archivo:** `commons/models.py`

Nuevo modelo siguiendo la estructura de `T_admin`:

```python
class T_consulta(models.Model):
    AREA_CHOICES = [
        ('sistemas',  'Sistemas'),
        ('contable',  'Contable'),
        ('direccion', 'Dirección'),
        ('rrhh',      'RRHH'),
    ]
    NIVEL_CHOICES = [
        ('basico',      'Básico'),
        ('intermedio',  'Intermedio'),
        ('avanzado',    'Avanzado'),
    ]
    ESTADO_CHOICES = [
        ('activo',   'Activo'),
        ('inactivo', 'Inactivo'),
    ]
    perfil       = models.OneToOneField(T_perfil, on_delete=models.CASCADE, related_name='consulta')
    area         = models.CharField(max_length=20, choices=AREA_CHOICES)
    nivel_acceso = models.CharField(max_length=20, choices=NIVEL_CHOICES)
    esta         = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='activo')
```

Se genera una migración nueva. No toca modelos existentes.

---

## Form — `ConsultaForm`

**Archivo:** `usuarios/forms.py`

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
```

La información de perfil base (nombre, DNI, email, etc.) usa el `PerfilForm` existente, igual que todos los demás roles.

---

## Vistas — `usuarios/views.py`

| Función | Método | Decoradores | Responsabilidad |
|---|---|---|---|
| `consultas()` | GET | `@login_required` | Lista T_consulta con select_related a perfil |
| `crear_consulta()` | POST | `@login_required` `@bloquear_si_consulta` | Crea User + T_perfil (rol='consulta') + T_consulta + permisos predefinidos |
| `obtener_consulta(consulta_id)` | GET | `@login_required` `@bloquear_si_consulta` | Retorna JSON con datos del usuario para modal de edición |
| `editar_consulta(consulta_id)` | POST | `@login_required` `@bloquear_si_consulta` | Actualiza campos de T_perfil y T_consulta |
| `eliminar_consulta(consulta_id)` | POST | `@login_required` `@bloquear_si_consulta` | Elimina T_consulta → T_perfil → User en cascada |

**Generación de username:** primeras 3 letras de nombre + primeras 3 de apellido, sufijo numérico secuencial si hay conflicto. Mismo algoritmo que los demás roles.

---

## URLs — `IOTPMV/urls.py`

```python
path('consultas/',                               usuarios_views.consultas,          name='consultas'),
path('api/consulta/crear/',                      usuarios_views.crear_consulta,     name='api_crear_consulta'),
path('api/consulta/<int:consulta_id>/',          usuarios_views.obtener_consulta,   name='api_obtener_consulta'),
path('api/consulta/editar/<int:consulta_id>/',   usuarios_views.editar_consulta,    name='api_editar_consulta'),
path('api/consulta/eliminar/<int:consulta_id>/', usuarios_views.eliminar_consulta,  name='api_eliminar_consulta'),
```

---

## Template — `usuarios/templates/consulta.html`

- Extiende `base.html`, misma estructura que `administradores.html`
- Guards `{% if can_view %}` / `{% if can_edit %}` con el sistema de permisos existente
- **Tabla:** columnas Nombre, Apellido, DNI, Email, Área, Nivel de Acceso, Estado, Acciones
- **Modal crear:** `PerfilForm` + `ConsultaForm`
- **Modal editar:** mismos campos precargados vía AJAX (`obtener_consulta`)
- **Botón eliminar** por fila con confirmación

---

## Complementos

### `admin_dashboard.html`
Agregar card "Usuarios de Consulta" con enlace a `/consultas/` junto a las demás tarjetas de gestión de usuarios.

### `poblar_permisos.py`
Agregar permiso `('consultas', 'ver')` y `('consultas', 'editar')` al rol `admin` para que el módulo aparezca y sea editable desde el dashboard.

---

## Archivos a crear/modificar

| Acción | Archivo |
|---|---|
| Modificar | `commons/models.py` |
| Crear | `commons/migrations/XXXX_t_consulta.py` |
| Modificar | `usuarios/forms.py` |
| Modificar | `usuarios/views.py` |
| Modificar | `IOTPMV/urls.py` |
| Crear | `usuarios/templates/consulta.html` |
| Modificar | `usuarios/templates/admin_dashboard.html` |
| Modificar | `commons/management/commands/poblar_permisos.py` |

---

## Fuera de alcance

- Cambios en permisos de lectura del rol `consulta` (ya están definidos y funcionan)
- Campos adicionales en `T_consulta` (se agregan en iteraciones futuras)
- Migración de usuarios consulta existentes (se hace manualmente o con script aparte)
