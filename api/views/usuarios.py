from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from commons.models import T_perfil
from api.serializers.usuarios import PerfilSerializer
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q


class PerfilPagination(PageNumberPagination):
    page_size_query_param = 'length'
    page_query_param = 'start'

    def paginate_queryset(self, queryset, request, view=None):
        try:
            self.offset = int(request.query_params.get('start', 0))
            self.limit = int(request.query_params.get('length', self.page_size))
            self.count = queryset.count()
            self.request = request
            return list(queryset[self.offset:self.offset + self.limit])
        except (ValueError, TypeError):
            return None

    def get_paginated_response(self, data):
        return Response({
            'recordsTotal': self.count,
            'recordsFiltered': self.count,
            'data': data
        })

class PerfilViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = T_perfil.objects.all()
    serializer_class = PerfilSerializer
    pagination_class = PerfilPagination

    @action(detail=False, methods=['get'], url_path='filtrar')
    def filtrar(self, request):
        rol = request.GET.getlist('rol', [])
        tipo_dni = request.GET.getlist('tipo_dni', [])
        search = request.GET.get('search[value]', '').strip()

        perfiles = T_perfil.objects.all()

        if rol:
            perfiles = perfiles.filter(rol__in=rol)

        if tipo_dni:
            perfiles = perfiles.filter(tipo_dni__in = tipo_dni)

        if search:
            perfiles = perfiles.filter(
                Q(user__username__icontains=search) |
                Q(nom__icontains=search) |
                Q(apelli__icontains=search) |
                Q(mail__icontains=search) |
                Q(rol__icontains=search) |
                Q(dni__icontains=search)
            )

        paginated = self.paginate_queryset(perfiles)
        serializer = PerfilSerializer(paginated, many=True)
        return self.get_paginated_response(serializer.data)        
