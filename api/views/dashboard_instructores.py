import io
from datetime import timedelta

from django.db.models import Count, Max, Q, Subquery, OuterRef, IntegerField
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
    dias_efectivo = dias if dias is not None else 999
    if dias_efectivo < 3:
        return 'verde'
    if dias_efectivo < 6:
        return 'amarillo'
    return 'rojo'


def _autorizado(request) -> bool:
    mixin = PermisosMixin()
    mixin.modulo = 'seguimiento'
    return mixin.get_permission_actions(request).get('ver', False)


def _annotate_ultima_actividad(qs):
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


def _annotate_counts(qs):
    """Anota conteos de fichas, aprendices y alertas a nivel SQL
    para evitar N+1 queries por instructor."""
    return qs.annotate(
        evidencias_esperadas_apre=Count(
            't_ficha__t_apre__t_documentfolderaprendiz',
            filter=Q(t_ficha__t_apre__t_documentfolderaprendiz__tipo='documento'),
            distinct=True,
        ),
        evidencias_cargadas_apre=Count(
            't_ficha__t_apre__t_documentfolderaprendiz',
            filter=Q(
                t_ficha__t_apre__t_documentfolderaprendiz__tipo='documento',
                t_ficha__t_apre__t_documentfolderaprendiz__documento__isnull=False,
            ),
            distinct=True,
        ),
        fichas_count=Count('t_ficha', distinct=True),
        apre_total=Count('t_ficha__t_apre', distinct=True),
        apre_activos=Count(
            't_ficha__t_apre',
            filter=Q(t_ficha__t_apre__esta='activo'),
            distinct=True,
        ),
        alertas_count=Count(
            'perfil__user__notificaciones',
            filter=Q(
                perfil__user__notificaciones__origen_tipo__startswith='inactividad_',
                perfil__user__notificaciones__leida=False,
            ),
            distinct=True,
        ),
        evidencias_esperadas_ficha=Count(
            't_ficha__t_documentfolder',
            filter=Q(t_ficha__t_documentfolder__tipo='documento'),
            distinct=True,
        ),
        evidencias_cargadas_ficha=Count(
            't_ficha__t_documentfolder',
            filter=Q(
                t_ficha__t_documentfolder__tipo='documento',
                t_ficha__t_documentfolder__documento__isnull=False,
            ),
            distinct=True,
        ),
    )


def _filtrar_por_semaforo(qs, semaforo: str):
    if semaforo not in ('verde', 'amarillo', 'rojo'):
        return qs

    ahora = timezone.now()
    limite_verde = ahora - timedelta(days=3)
    limite_amarillo = ahora - timedelta(days=6)

    if semaforo == 'verde':
        return qs.filter(ultima_actividad_sql__gte=limite_verde)
    if semaforo == 'amarillo':
        return qs.filter(
            ultima_actividad_sql__lt=limite_verde,
            ultima_actividad_sql__gte=limite_amarillo,
        )
    return qs.filter(
        Q(ultima_actividad_sql__lt=limite_amarillo)
        | Q(ultima_actividad_sql__isnull=True),
    )


def _porcentaje_evidencias(instructor_id: int) -> tuple[int, int, float]:
    """Cuenta evidencias de aprendices (las de ficha ya van anotadas)."""
    folders_apre = T_DocumentFolderAprendiz.objects.filter(
        aprendiz__ficha__instru_id=instructor_id, tipo='documento',
    ).aggregate(
        total=Count('id'),
        cargados=Count('id', filter=Q(documento__isnull=False)),
    )
    return (
        folders_apre['total'] or 0,
        folders_apre['cargados'] or 0,
    )


def _instructor_to_row(ins) -> dict:
    """Convierte un instructor anotado en su fila para el dashboard.
    Usa los valores anotados en el queryset para evitar queries extra."""

    ahora = timezone.now()

    # Usar anotaciones SQL si están disponibles
    ua = getattr(ins, 'ultima_actividad_sql', None)
    if ua is None:
        ua = ultima_actividad(ins)
        dias = dias_sin_actividad(ins)
    else:
        dias = (ahora - ua).days if ua else None

    # Evidencias: ficha viene anotada, aprendiz se calcula aparte
    ev_esp_ficha = getattr(ins, 'evidencias_esperadas_ficha', 0) or 0
    ev_car_ficha = getattr(ins, 'evidencias_cargadas_ficha', 0) or 0

    apre_esp = getattr(ins, 'evidencias_esperadas_apre', 0) or 0
    apre_car = getattr(ins, 'evidencias_cargadas_apre', 0) or 0
    esperados = ev_esp_ficha + apre_esp
    cargados = ev_car_ficha + apre_car
    pct = round((cargados / esperados) * 100, 1) if esperados else 0.0

    # Conteos anotados
    fichas_count = getattr(ins, 'fichas_count', 0) or 0
    apre_total = getattr(ins, 'apre_total', 0) or 0
    apre_activos = getattr(ins, 'apre_activos', 0) or 0
    alertas = getattr(ins, 'alertas_count', 0) or 0

    return {
        'instructor_id': ins.id,
        'nombre': f'{ins.perfil.nom} {ins.perfil.apelli}'.strip() if ins.perfil else '—',
        'dni': ins.perfil.dni if ins.perfil else None,
        'mail': ins.perfil.mail if ins.perfil else None,
        'estado': ins.esta,
        'ultimo_acceso': ua.isoformat() if ua else None,
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


# Mapa de columna DataTables → campo Django para ordenamiento
ORDERABLE_COLUMNS = {
    1: 'perfil__nom',           # Instructor (nombre)
    2: 'perfil__dni',           # DNI
    3: 'ultima_actividad_sql',  # Último acceso
    4: 'ultima_actividad_sql',  # Días sin actividad (inverso)
    7: 'fichas_count',          # Fichas
}


def _apply_ordering(qs, request):
    """Lee los parámetros order[0][column] y order[0][dir] de DataTables
    y aplica el ORDER BY correspondiente."""
    try:
        col_idx = int(request.GET.get('order[0][column]', 1))
        direction = request.GET.get('order[0][dir]', 'asc')
    except (ValueError, TypeError):
        col_idx, direction = 1, 'asc'

    field = ORDERABLE_COLUMNS.get(col_idx, 'perfil__nom')

    # Invertir dirección para dias_sin_actividad (más días = fecha más vieja)
    if col_idx == 4:
        direction = 'desc' if direction == 'asc' else 'asc'

    if direction == 'desc':
        field = f'-{field}'

    return qs.order_by(field)


def _build_rows():
    """Construye TODAS las filas (sin paginar). Usado solo por exportación."""
    qs = T_instru.objects.select_related('perfil__user').all()
    qs = _annotate_ultima_actividad(qs)
    qs = _annotate_counts(qs)
    return [_instructor_to_row(ins) for ins in qs]


# ============================================================================
# ENDPOINTS DEL DASHBOARD
# ============================================================================

class DashboardInstructoresView(APIView):
    """Listado paginado de instructores con server-side processing."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _autorizado(request):
            return Response({'detail': 'No autorizado'}, status=403)

        qs = T_instru.objects.select_related('perfil__user').all()

        # Anotar actividad y conteos (evita N+1)
        qs = _annotate_ultima_actividad(qs)
        qs = _annotate_counts(qs)

        # Filtro search
        search = request.GET.get('search[value]', '').strip()
        if search:
            qs = qs.filter(
                Q(perfil__nom__icontains=search)
                | Q(perfil__apelli__icontains=search)
                | Q(perfil__dni__icontains=search)
                | Q(perfil__mail__icontains=search),
            )

        # Filtro semáforo
        semaforo = request.GET.get('semaforo', '').strip()
        if semaforo in ('verde', 'amarillo', 'rojo'):
            qs = _filtrar_por_semaforo(qs, semaforo)

        # Ordenamiento dinámico
        qs = _apply_ordering(qs, request)

        # Paginar
        paginator = DataTablesPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        if page is None:
            return Response({
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'data': [],
            })

        rows = [_instructor_to_row(ins) for ins in page]
        return paginator.get_paginated_response(rows)


class KpiInstructoresView(APIView):
    """KPIs agregados del dashboard de instructores."""
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
    """Exporta a Excel TODO el listado de instructores."""
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
    """Lista paginada de aprendices próximos a cumplir 18."""
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

        search = request.GET.get('search[value]', '').strip()
        if search:
            candidatos = candidatos.filter(
                Q(perfil__nom__icontains=search)
                | Q(perfil__apelli__icontains=search)
                | Q(perfil__dni__icontains=search),
            )

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

        estado_filtro = request.GET.get('estado', '').strip()
        if estado_filtro in ('proximo', 'cumple_hoy', 'al_dia', 'riesgo'):
            all_rows = [r for r in all_rows if r['estado'] == estado_filtro]

        all_rows.sort(key=lambda r: r['dias_para_18'])

        try:
            start = int(request.GET.get('start', 0))
            length = int(request.GET.get('length', 10))
        except ValueError:
            start, length = 0, 10

        total = len(all_rows)
        if length > 0:
            paginated = all_rows[start:start + length]
        else:
            paginated = all_rows

        return Response({
            'recordsTotal': total,
            'recordsFiltered': total,
            'data': paginated,
        })
class KpiMayoriaEdadView(APIView):
    """KPIs de mayoría de edad."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _autorizado(request):
            return Response({'detail': 'No autorizado'}, status=403)

        try:
            ventana_futura = int(request.GET.get('futura', 60))
            ventana_pasada = int(request.GET.get('pasada', 60))
        except ValueError:
            ventana_futura, ventana_pasada = 60, 60

        candidatos = T_apre.objects.select_related('perfil').filter(
            esta='activo', perfil__fecha_naci__isnull=False,
        )

        counts = {'total': 0, 'proximo': 0, 'cumple_hoy': 0, 'riesgo': 0, 'al_dia': 0}
        for apre in candidatos:
            d = dias_para_18(apre)
            if d is None or d > ventana_futura or d < -ventana_pasada:
                continue
            counts['total'] += 1
            if d > 0:
                counts['proximo'] += 1
            elif d == 0:
                counts['cumple_hoy'] += 1
            elif tiene_cc_actualizado(apre):
                counts['al_dia'] += 1
            else:
                counts['riesgo'] += 1

        return Response(counts)

class InstructorDetalleView(APIView):
    """Drill-down: detalle de un instructor."""
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
