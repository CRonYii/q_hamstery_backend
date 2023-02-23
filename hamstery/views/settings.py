from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from django.http import JsonResponse

from ..models import HamsterySettings
from ..serializers import HamsterySettingsSerializer

# Create your views here.


class HamsterySettingsView(mixins.RetrieveModelMixin,
                           mixins.UpdateModelMixin,
                           viewsets.GenericViewSet):
    serializer_class = HamsterySettingsSerializer

    def get_queryset(self):
        return None

    def get_object(self):
        return HamsterySettings.singleton()

    @action(methods=['get'], detail=True)
    def qbt_test_connection(self, request, pk=None):
        from hamstery.qbittorrent import qbt
        [result, msg] = qbt.test_connection()
        return JsonResponse({'status': result, 'message': msg})

    @action(methods=['get'], detail=True)
    def plex_test_connection(self, request, pk=None):
        from hamstery.plex import plex_manager
        [result, msg] = plex_manager.test_connection()
        return JsonResponse({'status': result, 'message': msg})
