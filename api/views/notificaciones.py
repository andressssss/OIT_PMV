from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from tasks.models import T_notifi
from api.serializers.notificaciones import NotificacionSerializer


class NotificacionesViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        only_unread = request.query_params.get('no_leidas') == '1'
        limit = int(request.query_params.get('limit', 20))
        qs = T_notifi.objects.filter(usuario=request.user)
        if only_unread:
            qs = qs.filter(leida=False)
        qs = qs[:limit]
        return Response(NotificacionSerializer(qs, many=True).data)

    @action(detail=False, methods=['get'], url_path='resumen')
    def resumen(self, request):
        qs = T_notifi.objects.filter(usuario=request.user, leida=False, resuelta=False)
        return Response({
            'no_leidas': qs.count(),
            'ultimas': NotificacionSerializer(qs[:5], many=True).data,
        })

    @action(detail=True, methods=['post'], url_path='marcar-leida')
    def marcar_leida(self, request, pk=None):
        try:
            n = T_notifi.objects.get(pk=pk, usuario=request.user)
        except T_notifi.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        n.marcar_leida()
        return Response({'ok': True})
    
    @action(detail=True, methods=['post'], url_path='marcar-resuelta')
    def marcar_resuelta(self, request, pk=None):
        from commons.models import T_perfil, T_ficha, T_apre
        try:
            n = T_notifi.objects.get(pk=pk)
        except T_notifi.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        perfil = T_perfil.objects.filter(user=request.user).first()
        if not perfil:
            return Response({'error': 'Sin perfil'}, status=status.HTTP_403_FORBIDDEN)
        es_admin = perfil.rol == 'admin'
        es_destinatario = (n.usuario_id == request.user.id)
        es_instructor_ficha = False
        if not (es_admin or es_destinatario):
            if n.origen_tipo and n.origen_tipo.startswith('mayoria_edad') and n.origen_id:
                apre = T_apre.objects.filter(id=n.origen_id).select_related('ficha__instru__perfil').first()
                if apre and apre.ficha and apre.ficha.instru:
                    es_instructor_ficha = (apre.ficha.instru.perfil_id == perfil.id)
        if not (es_admin or es_destinatario or es_instructor_ficha):
            return Response({'error': 'No tiene permisos'}, status=status.HTTP_403_FORBIDDEN)
        n.marcar_resuelta(usuario=request.user)
        return Response({'ok': True})
    
    @action(detail=False, methods=['get'], url_path=r'ficha/(?P<ficha_id>\d+)')
    def por_ficha(self, request, ficha_id=None):
        """Lista las notificaciones tipo mayoria_edad de los aprendices de una ficha.

        Permisos: admin O instructor asignado a la ficha.
        Devuelve solo las NO resueltas.
        """
        from commons.models import T_perfil, T_ficha, T_apre

        # 1. Validar perfil
        perfil = T_perfil.objects.filter(user=request.user).first()
        if not perfil:
            return Response(
                {'error': 'Su usuario no tiene perfil asociado.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # 2. Traer la ficha
        try:
            ficha = T_ficha.objects.select_related('instru__perfil').get(id=ficha_id)
        except T_ficha.DoesNotExist:
            return Response(
                {'error': 'Ficha no encontrada.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # 3. Validar permisos: admin OR instructor de la ficha
        es_admin = perfil.rol == 'admin'
        es_instructor_ficha = (
            ficha.instru is not None
            and ficha.instru.perfil_id == perfil.id
        )

        if not (es_admin or es_instructor_ficha):
            return Response(
                {'error': 'No tiene permisos para ver las alertas de esta ficha.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # 4. Obtener IDs de los aprendices de la ficha
        aprendices_ids = list(
            T_apre.objects.filter(ficha_id=ficha_id).values_list('id', flat=True)
        )

        # 5. Traer las notificaciones tipo mayoria_edad NO resueltas
        # Nota: usamos __startswith porque la task crea notificaciones con
        # origen_tipo = regla.tipo, que puede ser 'mayoria_edad_preventiva',
        # 'mayoria_edad_dia0' o 'mayoria_edad_riesgo'.
        notificaciones = T_notifi.objects.filter(
            origen_tipo__startswith='mayoria_edad',
            origen_id__in=aprendices_ids,
            resuelta=False,
        ).order_by('-creada_en')

        return Response(NotificacionSerializer(notificaciones, many=True).data)
    
    
    


    @action(detail=False, methods=['post'], url_path='marcar-todas-leidas')
    def marcar_todas_leidas(self, request):
        T_notifi.objects.filter(
            usuario=request.user, leida=False
        ).update(leida=True, leida_en=timezone.now())
        return Response({'ok': True})
