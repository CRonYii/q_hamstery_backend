from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from asgiref.sync import async_to_sync

from hamstery.qbittorrent import download_episode

from ..forms import DownloadForm, TMDBForm
from ..serializers import TvLibrarySerializer, TvStorageSerializer, TvShowSerializer, TvSeasonSerializer, TvEpisodeSerializer
from ..models import TvLibrary, TvStorage, TvShow, TvSeason, TvSeason, TvEpisode

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

    @action(methods=['post'], detail=True, url_name='add-show', url_path='add-show')
    def add_show(self, request, pk=None):
        storage: TvStorage = TvStorage.objects.prefetch_related('lib').get(pk=pk)
        form = TMDBForm(request.POST)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
        tmdb_id = form.cleaned_data['tmdb_id']
        if storage.shows.filter(tmdb_id__exact=tmdb_id).exists():
            return Response('Show already exists', status=status.HTTP_400_BAD_REQUEST)
        async_to_sync(TvShow.objects.create_or_update_by_tmdb_id)(storage, tmdb_id)
        return Response('Ok')

class TvShowView(viewsets.ReadOnlyModelViewSet):
    queryset = TvShow.objects.all()
    serializer_class = TvShowSerializer

class TvSeasonView(viewsets.ReadOnlyModelViewSet):
    queryset = TvSeason.objects.all()
    serializer_class = TvSeasonSerializer

class TvEpisodeView(viewsets.ReadOnlyModelViewSet):
    queryset = TvEpisode.objects.all()
    serializer_class = TvEpisodeSerializer

    @action(methods=['post'], detail=True)
    def download(self, request, pk=None):
        episode = self.get_object()
        form = DownloadForm(request.POST)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
        url = form.cleaned_data['url']
        if download_episode(episode, url):
            return Response('Ok')
        else:
            return Response('Invalid URL', status=status.HTTP_400_BAD_REQUEST)