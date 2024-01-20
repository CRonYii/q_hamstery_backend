from typing import OrderedDict

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class HamsteryPaginator(PageNumberPagination):
    page_size = 25
    
    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('page_size', self.page_size),
            ('page', self.page.number),
            ('results', data)
        ]))