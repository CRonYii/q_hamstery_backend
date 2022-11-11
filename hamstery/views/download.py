from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from asgiref.sync import async_to_sync

from ..serializers import TvDownloadSerializer
from ..models import TvDownload

# Create your views here.


class TvDownloadView(viewsets.ReadOnlyModelViewSet):
    queryset = TvDownload.objects.all()
    serializer_class = TvDownloadSerializer
    filterset_fields = ['done', 'episode']
