from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from ..serializers import TorznabIndexerSerializer
from ..models.indexer import TorznabIndexer

# Create your views here.

class TorznabIndexerView(viewsets.ModelViewSet):
    queryset = TorznabIndexer.objects.all()
    serializer_class = TorznabIndexerSerializer

    @action(methods=['get'], detail=True)
    def search(self, request, pk=None):
        indexer: TorznabIndexer = self.get_object()
        query = request.GET['query'] if 'query' in request.GET else ''
        result = TorznabIndexer.search(indexer, query)
        if result['success'] is True:
            return Response(result['data'])
        else:
            return Response(result['errors'], status=status.HTTP_400_BAD_REQUEST)