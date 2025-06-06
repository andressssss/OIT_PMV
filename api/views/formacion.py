from rest_framework.viewsets import ViewSet, ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from api.serializers.formacion import RapsCreateSerializer, RAPSerializer, CompetenciaSerializer, FichaSerializer
from commons.models import T_raps, T_compe, T_ficha

import logging

logger = logging.getLogger(__name__)

class RapsViewSet(ModelViewSet):
    queryset = T_raps.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve', 'partial_update', 'update']:
            return RAPSerializer  # serializer para leer y editar
        if self.action == 'create':
            return RapsCreateSerializer  # serializer para creación
        return RAPSerializer  # fallback

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({
                'status': 'success',
                'message': 'RAP creado correctamente',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'status': 'error',
            'message': 'Formulario inválido',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class CompetenciasViewSet(ModelViewSet):
    serializer_class = CompetenciaSerializer
    queryset = T_compe.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        programa_id = self.request.query_params.get('programa')
        logger.warning(f"programa_id recibido: {programa_id}")
        if programa_id:
            queryset = queryset.filter(progra__id=programa_id)
        return queryset

class FichasViewSet(ModelViewSet):
    queryset = T_ficha.objects.all()
    serializer_class = FichaSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='por_programa/(?P<programa_id>[^/.]+)')
    def fichas_por_programa(self, request, programa_id=None):
        fichas = self.get_queryset().filter(progra = programa_id)
        serializer = self.get_serializer(fichas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)