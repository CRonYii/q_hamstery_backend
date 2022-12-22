from rest_framework import viewsets, status
from rest_framework.response import Response

from ..models import TvDownload, MonitoredTvDownload
from ..qbittorrent import qbt_client
from ..serializers import TvDownloadSerializer, MonitoredTvDownloadSerializer

# Create your views here.


class TvDownloadView(viewsets.GenericViewSet):
    queryset = TvDownload.objects.all()
    serializer_class = TvDownloadSerializer
    filterset_fields = {
        'done': ['exact'],
        'episode': ['exact', 'in'],
    }

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

    def perform_destroy(self, download: TvDownload):
        if download.done is True and download.episode:
            download.episode.remove_episode() # remove episode will delete download for us
            download.episode.save()
        else:
            download.cancel()

    def append_extra_info(self, download):
        hash = '|'.join(map(lambda d: d['hash'], download))
        info = qbt_client.torrents_info(torrent_hashes=hash)
        for d in download:
            i = next((x for x in info if x['hash'] == d['hash']), None)
            if i is None:
                continue
            extra = {}
            extra['progress'] = i['progress']
            extra['dlspeed'] = i['dlspeed']
            extra['completed'] = i['completed']
            extra['completion_on'] = i['completion_on']
            extra['size'] = i['total_size']
            extra['eta'] = i['eta']
            extra['ratio'] = i['ratio']
            extra['uploaded'] = i['uploaded']
            extra['upspeed'] = i['upspeed']
            d['extra_info'] = extra
        return download

class MonitoredDownloadView(viewsets.ReadOnlyModelViewSet):
    queryset = MonitoredTvDownload.objects.all()
    serializer_class = MonitoredTvDownloadSerializer
    filterset_fields = {
        'subscription': ['exact'],
    }
