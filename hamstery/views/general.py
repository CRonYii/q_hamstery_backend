from typing import OrderedDict

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class HamsteryPaginator(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'

    used_paginator = False
    
    def get_paginated_response(self, data):
        if self.used_paginator:
            return Response(OrderedDict([
                ('count', self.page.paginator.count),
                ('page_size', self.page_size),
                ('page', self.page.number),
                ('results', data)
            ]))
        else:
            return Response(data)
    
    def paginate_queryset(self, queryset, request, view=None):
        if self.page_query_param not in request.query_params:
            self.used_paginator = False
            return queryset
        self.used_paginator = True
        return super().paginate_queryset(queryset, request, view)
