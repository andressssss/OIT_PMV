import io
from datetime import timedelta

from django.db.models import Count, Max, Q
from django.db.models.functions import Coalesce, Greatest
from django.http import HttpResponse
from django.utils import timezone
from openpyxl import Workbook
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from commons.mixins import PermisosMixin
from commons.models import (
    T_DocumentFolder, T_DocumentFolderAprendiz, T_apre, T_ficha, T_instru,
)
from commons.pagination import DataTablesPagination
from tasks.models import T_notifi
from tasks.services.inactividad import (
    ACCIONES_CONSIDERADAS, dias_sin_actividad, ultima_actividad,
)
from tasks.services.mayoria_edad import (
    dias_para_18, fecha_18, tiene_cc_actualizado,
)


# ============================================================================
# HELPERS
# ============================================================================

def _semaforo(porcentaje: float, dias: int | None) -> str:
    """verde/amarillo/rojo según días sin actividad (umbrales 3 y 6).

    El parámetro `porcentaje` se mantiene por compatibilidad con la firma
    anterior, pero ya no afecta el resultado (el semáforo depende solo de
    días desde el fix del PR #30).
    """
    dias_efectivo = dias if dias is not None else 999
    if dias_efectivo < 3:
        return 'verde'
    if dias_efectivo < 6:
        return 'amarillo'
    return 'rojo'


def _autorizado(request) -> bool:
    """Verifica que el perfil tenga el permiso (seguimiento, ver)."""
    mixin = PermisosMixin()
    mixin.modulo = 'seguimiento'
    return mixin.get_permission_actions(request).get('ver', False)


def _annotate_ultima_actividad(qs):
    """Anota `ultima_actividad_sql` que replica EXACTAMENTE el cálculo de
    tasks.services.inactividad.ultima_actividad() pero a nivel SQL.

    Esto permite filtrar y agregar por semáforo en la base de datos sin
    recorrer todos los instructores en Python.

    Nota técnica: Greatest() con NULL se comporta distinto en MySQL/MariaDB
    respecto a Postgres. El truco `Greatest(Coalesce(a, b), Coalesce(b, a))`
    maneja los NULLs correctamente en ambos motores:
      - si ambas fechas son NULL → resultado NULL
      - si solo una es NULL → resultado = la otra
      - si ninguna es NULL → resultado = la mayor de las dos
    """
    return qs.annotate(
        last_audit_dt=Max(
            'perfil__user__auditlog__timestamp',
            filter=Q(perfil__user__auditlog__action__in=ACCIONES_CONSIDERADAS),
        ),
    ).annotate(
        ultima_actividad_sql=Greatest(
            Coalesce('perfil__user__last_login', 'last_audit_dt'),
            Coalesce('last_audit_dt', 'perfil__user__last_login'),
        ),
    )


def _filtrar_por_semaforo(qs, semaforo: str):
    """Filtra un queryset ya anotado con `ultima_actividad_sql` por color de
    semáforo. Usa los mismos umbrales que _semaforo() (3 y 6 días).
    """
    if semaforo not in ('verde', 'amarillo', 'rojo'):
        return qs

    ahora = timezone.now()
    limite_verde = ahora - timedelta(days=3)
    limite_amarillo = ahora - timedelta(days=6)

    if semaforo == 'verde':
        # Menos de 3 días sin actividad
        return qs.filter(ultima_actividad_sql__gte=limite_verde)

    if semaforo == 'amarillo':
        # Entre 3 y 6 días sin actividad
        return qs.filter(
            ultima_actividad_sql__lt=limite_verde,
            ultima_actividad_sql__gte=limite_amarillo,
        )

    # rojo: 6+ días sin actividad o sin actividad registrada
    return qs.filter(
        Q(ultima_actividad_sql__lt=limite_amarillo)
        | Q(ultima_actividad_sql__isnull=True),
    )


def _porcentaje_evidencias(instructor_id: int) -> tuple[int, int, float]:
    """Cuenta nodos de tipo documento (esperados) y los que tienen archivo
    cargado, sumando portafolios de ficha y de aprendices del instructor.
    Devuelve (cargados, esperados, porcentaje 0-100).
    """
    folders_ficha = T_DocumentFolder.objects.filter(
        ficha__instru_id=instructor_id, tipo='documento',
    ).aggregate(
        total=Count('id'),
        cargados=Count('id', filter=Q(documento__isnull=False)),
    )

    folders_apre = T_DocumentFolderAprendiz.objects.filter(
        aprendiz__ficha__instru_id=instructor_id, tipo='documento',
    ).aggregate(
        total=Count('id'),
        cargados=Count('id', filter=Q(documento__isnull=False)),
    )

    esperados = (folders_ficha['total'] or 0) + (folders_apre['total'] or 0)
    cargados = (folders_ficha['cargados'] or 0) + (folders_apre['cargados'] or 0)
    pct = round((cargados / esperados) * 100, 1) if esperados else 0.0
    return cargados, esperados, pct


def _instructor_to_row(ins: T_instru) -> dict:
    """Convierte un instructor en su fila completa para el dashboard.

    OJO: ejecuta varias queries adicionales por instructor (evidencias,
    fichas, aprendices, alertas). Solo se debe llamar para los instructores
    de la página actual, NO para los 1116 de una vez.
    """
    user = ins.perfil.user if ins.perfil else None
    cargados, esperados, pct = _porcentaje_evidencias(ins.id)
    dias = dias_sin_actividad(ins)
    ultima = ultima_actividad(ins)

    fichas_count = T_ficha.objects.filter(instru=ins).count()
    apre_total = T_apre.objects.filter(ficha__instru=ins).count()
    apre_activos = T_apre.objects.filter(
        ficha__instru=ins, esta='activo',
    ).count()

    alertas = T_notifi.objects.filter(
        usuario=user,
        origen_tipo__startswith='inactividad_',
        leida=False,
    ).count() if user else 0

    return {
        'instructor_id': ins.id,
        'nombre': f'{ins.perfil.nom} {ins.perfil.apelli}'.strip() if ins.perfil else '—',
        'dni': ins.perfil.dni if ins.perfil else None,
        'mail': ins.perfil.mail if ins.perfil else None,
        'estado': ins.esta,
        'ultimo_acceso': ultima.isoformat() if ultima else None,
        'dias_sin_actividad': dias,
        'evidencias_cargadas': cargados,
        'evidencias_esperadas': esperados,
        'porcentaje_evidencias': pct,
        'fichas': fichas_count,
        'aprendices_matriculados': apre_total,
        'aprendices_activos': apre_activos,
        'alertas_abiertas': alertas,
        'semaforo': _semaforo(pct, dias),
    }


def _build_rows():
    """Construye TODAS las filas (sin paginar). Usado solo por el endpoint
    de exportación a Excel."""
    instructores = T_instru.objects.select_related('perfil__user').all()
    return [_instructor_to_row(ins) for ins in instructores]


# ============================================================================
# ENDPOINTS DEL DASHBOARD
# ============================================================================

class DashboardInstructoresView(APIView):
    """Listado paginado de instructores con server-side processing.

    Parámetros aceptados (estándar DataTables + extras):
      - draw, start, length, search[value]: estándar DataTables
      - semaforo=verde|amarillo|rojo: filtro custom por color

    Responde el formato que DataTables espera:
      {recordsTotal, recordsFiltered, data}
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _autorizado(request):
            return Response({'detail': 'No autorizado'}, status=403)

        qs = T_instru.objects.select_related('perfil__user').all()

        # Filtro search: nombre, apellido, dni, mail
        search = request.GET.get('search[value]', '').strip()
        if search:
            qs = qs.filter(
                Q(perfil__nom__icontains=search)
                | Q(perfil__apelli__icontains=search)
                | Q(perfil__dni__icontains=search)
                | Q(perfil__mail__icontains=search),
            )

        # Filtro semáforo: anota fechas y filtra a nivel SQL
        semaforo = request.GET.get('semaforo', '').strip()
        if semaforo in ('verde', 'amarillo', 'rojo'):
            qs = _annotate_ultima_actividad(qs)
            qs = _filtrar_por_semaforo(qs, semaforo)

        # Orden estable (DataTables además puede mandar order[0][column]
        # pero el orden por nombre cubre el caso por defecto)
        qs = qs.order_by('perfil__nom', 'perfil__apelli')

        # Paginar usando el paginator central (commons.pagination)
        paginator = DataTablesPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        if page is None:
            return Response({
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'data': [],
            })

        # SOLO ahora calcular datos pesados (solo para la página actual)
        rows = [_instructor_to_row(ins) for ins in page]
        return paginator.get_paginated_response(rows)


class KpiInstructoresView(APIView):
    """KPIs agregados del dashboard de instructores.

    Devuelve total y desglose por color de semáforo usando la misma
    annotation SQL que el endpoint de listado, garantizando que los
    conteos coincidan con lo que muestra la tabla al filtrar.

    Endpoint nuevo (no existía antes de este refactor).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _autorizado(request):
            return Response({'detail': 'No autorizado'}, status=403)

        ahora = timezone.now()
        limite_verde = ahora - timedelta(days=3)
        limite_amarillo = ahora - timedelta(days=6)

        qs = _annotate_ultima_actividad(T_instru.objects.all())

        total = qs.count()
        verde = qs.filter(ultima_actividad_sql__gte=limite_verde).count()
        amarillo = qs.filter(
            ultima_actividad_sql__lt=limite_verde,
            ultima_actividad_sql__gte=limite_amarillo,
        ).count()
        rojo = qs.filter(
            Q(ultima_actividad_sql__lt=limite_amarillo)
            | Q(ultima_actividad_sql__isnull=True),
        ).count()

        return Response({
            'total': total,
            'verde': verde,
            'amarillo': amarillo,
            'rojo': rojo,
        })


class DashboardInstructoresExportView(APIView):
    """Exporta a Excel TODO el listado de instructores (sin paginación).
    Para reportes el usuario espera el listado completo."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _autorizado(request):
            return Response({'detail': 'No autorizado'}, status=403)

        rows = _build_rows()
        wb = Workbook()
        ws = wb.active
        ws.title = 'Instructores'

        headers = [
            'ID', 'Nombre', 'DNI', 'Correo', 'Estado',
            'Último acceso', 'Días sin actividad',
            'Evidencias cargadas', 'Evidencias esperadas', '% Evidencias',
            'Fichas', 'Aprendices matriculados', 'Aprendices activos',
            'Alertas abiertas', 'Semáforo',
        ]
        ws.append(headers)
        for r in rows:
            ws.append([
                r['instructor_id'], r['nombre'], r['dni'], r['mail'], r['estado'],
                r['ultimo_acceso'] or '',
                r['dias_sin_actividad'] if r['dias_sin_actividad'] is not None else '',
                r['evidencias_cargadas'], r['evidencias_esperadas'], r['porcentaje_evidencias'],
                r['fichas'], r['aprendices_matriculados'], r['aprendices_activos'],
                r['alertas_abiertas'], r['semaforo'],
            ])

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        filename = f'instructores_{timezone.now().strftime("%Y%m%d_%H%M")}.xlsx'
        response = HttpResponse(
            buffer.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class AprendicesMayoriaEdadView(APIView):
    """Lista paginada de aprendices próximos a cumplir 18 con server-side.

    Parámetros:
      - draw, start, length, search[value]: estándar DataTables
      - estado=proximo|cumple_hoy|al_dia|riesgo: filtro custom
      - futura, pasada: días de ventana hacia futuro/pasado (default 60)

    Nota: las funciones fecha_18, dias_para_18 y tiene_cc_actualizado se
    calculan en Python (no se pueden expresar fácilmente en SQL), por lo
    que se itera el queryset ya filtrado por search/edad activa, y luego
    se pagina en Python.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _autorizado(request):
            return Response({'detail': 'No autorizado'}, status=403)

        try:
            ventana_futura = int(request.GET.get('futura', 60))
            ventana_pasada = int(request.GET.get('pasada', 60))
        except ValueError:
            ventana_futura, ventana_pasada = 60, 60

        candidatos = T_apre.objects.select_related(
            'perfil', 'ficha__instru__perfil',
        ).filter(esta='activo', perfil__fecha_naci__isnull=False)

        # Filtro search a nivel SQL antes del cálculo Python
        search = request.GET.get('search[value]', '').strip()
        if search:
            candidatos = candidatos.filter(
                Q(perfil__nom__icontains=search)
                | Q(perfil__apelli__icontains=search)
                | Q(perfil__dni__icontains=search),
            )

        # Calcular rows (las funciones de fecha_18 / cc_actualizado son Python)
        all_rows = []
        for apre in candidatos:
            d = dias_para_18(apre)
            if d is None:
                continue
            if d > ventana_futura or d < -ventana_pasada:
                continue

            f18 = fecha_18(apre)
            cc_ok = tiene_cc_actualizado(apre)

            if d > 0:
                estado = 'proximo'
            elif d == 0:
                estado = 'cumple_hoy'
            elif cc_ok:
                estado = 'al_dia'
            else:
                estado = 'riesgo'

            instru_perfil = (
                apre.ficha.instru.perfil
                if apre.ficha and apre.ficha.instru and apre.ficha.instru.perfil
                else None
            )

            all_rows.append({
                'aprendiz_id': apre.id,
                'nombre': f'{apre.perfil.nom} {apre.perfil.apelli}'.strip(),
                'dni': apre.perfil.dni,
                'tipo_dni': apre.perfil.tipo_dni,
                'fecha_naci': apre.perfil.fecha_naci.isoformat() if apre.perfil.fecha_naci else None,
                'fecha_18': f18.isoformat() if f18 else None,
                'dias_para_18': d,
                'cc_actualizado': cc_ok,
                'estado': estado,
                'ficha': apre.ficha.num if apre.ficha else None,
                'instructor': f'{instru_perfil.nom} {instru_perfil.apelli}'.strip() if instru_perfil else None,
            })

        # Filtro de estado (post-cálculo)
        estado_filtro = request.GET.get('estado', '').strip()
        if estado_filtro in ('proximo', 'cumple_hoy', 'al_dia', 'riesgo'):
            all_rows = [r for r in all_rows if r['estado'] == estado_filtro]

        # Orden estable
        all_rows.sort(key=lambda r: r['dias_para_18'])

        # Paginar en Python
        try:
            start = int(request.GET.get('start', 0))
            length = int(request.GET.get('length', 10))
        except ValueError:
            start, length = 0, 10

        total = len(all_rows)
        if length > 0:
            paginated = all_rows[start:start + length]
        else:
            paginated = all_rows  # length=-1 → todos

        return Response({
            'recordsTotal': total,
            'recordsFiltered': total,
            'data': paginated,
        })


class InstructorDetalleView(APIView):
    """Drill-down: detalle de un instructor con sus fichas y porcentajes.
    Sin cambios respecto al endpoint anterior."""
    permission_classes = [IsAuthenticated]

    def get(self, request, instructor_id: int):
        if not _autorizado(request):
            return Response({'detail': 'No autorizado'}, status=403)

        try:
            ins = T_instru.objects.select_related('perfil__user').get(pk=instructor_id)
        except T_instru.DoesNotExist:
            return Response({'detail': 'No existe'}, status=404)

        fichas = []
        for f in T_ficha.objects.filter(instru=ins).select_related('progra'):
            agg = T_DocumentFolder.objects.filter(ficha=f, tipo='documento').aggregate(
                total=Count('id'),
                cargados=Count('id', filter=Q(documento__isnull=False)),
            )
            esperados = agg['total'] or 0
            cargados = agg['cargados'] or 0
            pct = round((cargados / esperados) * 100, 1) if esperados else 0.0
            apre_total = T_apre.objects.filter(ficha=f).count()
            apre_activos = T_apre.objects.filter(ficha=f, esta='activo').count()
            fichas.append({
                'ficha_id': f.id,
                'numero': f.num,
                'programa': f.progra.nom if f.progra else None,
                'estado': f.esta,
                'evidencias_cargadas': cargados,
                'evidencias_esperadas': esperados,
                'porcentaje_evidencias': pct,
                'aprendices': apre_total,
                'aprendices_activos': apre_activos,
            })

        dias = dias_sin_actividad(ins)
        ultima = ultima_actividad(ins)

        return Response({
            'instructor_id': ins.id,
            'nombre': f'{ins.perfil.nom} {ins.perfil.apelli}'.strip() if ins.perfil else '—',
            'dni': ins.perfil.dni if ins.perfil else None,
            'mail': ins.perfil.mail if ins.perfil else None,
            'estado': ins.esta,
            'ultimo_acceso': ultima.isoformat() if ultima else None,
            'dias_sin_actividad': dias,
            'fichas': fichas,
        })