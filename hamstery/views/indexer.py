from rest_framework import viewsets
from rest_framework.decorators import action

from ..serializers import IndexerSerializer, TorznabSerializer
from ..models.indexer import Indexer, Torznab

# Create your views here.

class IndexerView(viewsets.ReadOnlyModelViewSet):
    queryset = Indexer.objects.all()
    serializer_class = IndexerSerializer

    @action(methods=['get'], detail=True)
    def search(self, request, pk=None):
        indexer: Indexer = self.get_object()
        query = request.GET['query'] if 'query' in request.GET else ''
        result = indexer.search(query)
        return result.into_response()


class TorznabView(viewsets.ModelViewSet):
    queryset = Torznab.objects.all()
    serializer_class = TorznabSerializer

    @action(methods=['get'], detail=True)
    def search(self, request, pk=None):
        indexer: Torznab = self.get_object()
        query = request.GET['query'] if 'query' in request.GET else ''
        result = indexer.search(query)
        return result.into_response()