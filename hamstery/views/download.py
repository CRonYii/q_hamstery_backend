from rest_framework import viewsets, status
from rest_framework.response import Response

from ..models import TvDownload
from ..qbittorrent import qbt_client
from ..serializers import TvDownloadSerializer

# Create your views here.


class TvDownloadView(viewsets.GenericViewSet):
    queryset = TvDownload.objects.all()
    serializer_class = TvDownloadSerializer
    filterset_fields = ['done', 'episode']

    def list(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        data = self.append_extra_info(serializer.data)
        return Response(data)

    def retrieve(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = self.append_extra_info([serializer.data])[0]
        return Response(data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.cancel()

    def append_extra_info(self, download):
        hash = '|'.join(map(lambda d: d['hash'], download))
        info = qbt_client.torrents_info(torrent_hashes=hash)
        for d in download:
            i = next((x for x in info if x['hash'] == d['hash']), None)
            if i is None:
                continue
            d['progress'] = i['progress']
            d['dlspeed'] = i['dlspeed']
            d['completed'] = i['completed']
            d['completion_on'] = i['completion_on']
            d['size'] = i['total_size']
            d['eta'] = i['eta']
            d['ratio'] = i['ratio']
            d['uploaded'] = i['uploaded']
            d['upspeed'] = i['upspeed']
        return download
