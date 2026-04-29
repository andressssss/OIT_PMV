import io
from django.db.models import Count, Q
from django.http import HttpResponse
from django.utils import timezone
from openpyxl import Workbook
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from commons.models import (
    T_instru, T_ficha, T_apre,
    T_DocumentFolder, T_DocumentFolderAprendiz,
)
from tasks.models import T_notifi
from tasks.services.inactividad import dias_sin_actividad, ultima_actividad
from tasks.services.mayoria_edad import (
    dias_para_18, fecha_18, tiene_cc_actualizado,
)


def _semaforo(porcentaje: float, dias: int | None) -> str:
    """verde / amarillo / rojo según %evidencias y días sin actividad."""
    dias_efectivo = dias if dias is not None else 999
    if porcentaje >= 80 and dias_efectivo < 3:
        return 'verde'
    if porcentaje >= 50 and dias_efectivo < 6:
        return 'amarillo'
    return 'rojo'


from commons.mixins import PermisosMixin


def _autorizado(request) -> bool:
    """Verifica que el perfil tenga el permiso (seguimiento, ver) en T_permi."""
    mixin = PermisosMixin()
    mixin.modulo = 'seguimiento'
    return mixin.get_permission_actions(request).get('ver', False)


def _porcentaje_evidencias(instructor_id: int) -> tuple[int, int, float]:
    """Cuenta nodos de tipo documento (esperados) y los que tienen archivo
    cargado, sumando portafolios de ficha y de aprendices del instructor.
    Devuelve (cargados, esperados, porcentaje 0-100)."""
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


def _build_rows():
    instructores = (
        T_instru.objects
        .select_related('perfil__user')
        .all()
    )

    rows = []
    for ins in instructores:
        user = ins.perfil.user if ins.perfil else None
        cargados, esperados, pct = _porcentaje_evidencias(ins.id)
        dias = dias_sin_actividad(ins)
        ultima = ultima_actividad(ins)

        fichas_qs = T_ficha.objects.filter(instru=ins)
        fichas_count = fichas_qs.count()
        apre_total = T_apre.objects.filter(ficha__instru=ins).count()
        apre_activos = T_apre.objects.filter(
            ficha__instru=ins, esta='activo'
        ).count()

        alertas = T_notifi.objects.filter(
            usuario=user,
            origen_tipo__startswith='inactividad_',
            leida=False,
        ).count() if user else 0

        rows.append({
            'instructor_id': ins.id,
            'nombre': f'{ins.perfil.nom} {ins.perfil.apelli}'.strip()
                      if ins.perfil else '—',
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
        })
    return rows


class DashboardInstructoresView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _autorizado(request):
            return Response({'detail': 'No autorizado'}, status=403)
        rows = _build_rows()
        return Response({'results': rows, 'total': len(rows)})


class DashboardInstructoresExportView(APIView):
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
                r['ultimo_acceso'] or '', r['dias_sin_actividad'] if r['dias_sin_actividad'] is not None else '',
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
    """Lista aprendices próximos a cumplir 18 (desde -ventana_pasada hasta
    +ventana_futura días). Incluye estado del CC para filtrar riesgo."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _autorizado(request):
            return Response({'detail': 'No autorizado'}, status=403)

        try:
            ventana_futura = int(request.query_params.get('futura', 60))
            ventana_pasada = int(request.query_params.get('pasada', 60))
        except ValueError:
            ventana_futura, ventana_pasada = 60, 60

        candidatos = T_apre.objects.select_related(
            'perfil', 'ficha__instru__perfil',
        ).filter(esta='activo', perfil__fecha_naci__isnull=False)

        rows = []
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

            rows.append({
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

        rows.sort(key=lambda r: r['dias_para_18'])
        return Response({'results': rows, 'total': len(rows)})


class InstructorDetalleView(APIView):
    """Drill-down: detalle de un instructor con sus fichas y porcentajes."""
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
            fichas.append({
                'ficha_id': f.id,
                'numero': f.num,
                'programa': f.progra.nom if f.progra_id else None,
                'estado': f.esta,
                'evidencias_cargadas': cargados,
                'evidencias_esperadas': esperados,
                'porcentaje_evidencias': pct,
                'aprendices': T_apre.objects.filter(ficha=f).count(),
                'aprendices_activos': T_apre.objects.filter(ficha=f, esta='activo').count(),
            })

        ultima = ultima_actividad(ins)
        dias = dias_sin_actividad(ins)

        return Response({
            'instructor_id': ins.id,
            'nombre': f'{ins.perfil.nom} {ins.perfil.apelli}'.strip(),
            'dni': ins.perfil.dni,
            'mail': ins.perfil.mail,
            'estado': ins.esta,
            'ultimo_acceso': ultima.isoformat() if ultima else None,
            'dias_sin_actividad': dias,
            'fichas': fichas,
        })
