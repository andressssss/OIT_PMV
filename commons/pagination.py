from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class DataTablesPagination(PageNumberPagination):
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
