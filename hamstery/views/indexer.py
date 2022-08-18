from rest_framework import viewsets
from rest_framework.decorators import action

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
        result = indexer.search(query)
        return result.into_response()