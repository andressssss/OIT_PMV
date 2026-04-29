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
        qs = T_notifi.objects.filter(usuario=request.user, leida=False)
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

    @action(detail=False, methods=['post'], url_path='marcar-todas-leidas')
    def marcar_todas_leidas(self, request):
        T_notifi.objects.filter(
            usuario=request.user, leida=False
        ).update(leida=True, leida_en=timezone.now())
        return Response({'ok': True})
