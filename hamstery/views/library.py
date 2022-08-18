from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from ..serializers import TvLibrarySerializer, TvStorageSerializer
from ..models import TvLibrary, TvStorage

# Create your views here.

class TvLibraryView(viewsets.ModelViewSet):
    queryset = TvLibrary.objects.all()
    serializer_class = TvLibrarySerializer

    @action(methods=['get'], detail=True)
    def scan(self, request, pk=None):
        lib: TvLibrary = self.get_object()
        return lib.scan().into_response()

class TvStorageView(viewsets.ModelViewSet):
    queryset = TvStorage.objects.all()
    serializer_class = TvStorageSerializer