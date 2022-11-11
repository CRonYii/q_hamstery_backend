from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from asgiref.sync import async_to_sync

from ..forms import DownloadForm, TMDBForm
from ..serializers import TvLibrarySerializer, TvStorageSerializer, TvShowSerializer, TvSeasonSerializer, TvEpisodeSerializer
from ..models import TvLibrary, TvStorage, TvShow, TvSeason, TvEpisode

# Create your views here.


class TvLibraryView(viewsets.ModelViewSet):
    queryset = TvLibrary.objects.all()
    serializer_class = TvLibrarySerializer

    @action(methods=['post'], detail=True)
    def scan(self, request, pk=None):
        lib: TvLibrary = self.get_object()
        return lib.scan().into_response()


class TvStorageView(viewsets.ModelViewSet):
    queryset = TvStorage.objects.all()
    serializer_class = TvStorageSerializer
    filterset_fields = ['lib']

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
    filterset_fields = ['storage']

    @action(methods=['post'], detail=True)
    def scan(self, request, pk=None):
        show: TvShow = TvShow.objects.prefetch_related('storage').get(pk=pk)
        print(show.storage.lib.lang)
        return show.scan().into_response()

class TvSeasonView(viewsets.ReadOnlyModelViewSet):
    queryset = TvSeason.objects.all()
    serializer_class = TvSeasonSerializer
    filterset_fields = ['show']

class TvEpisodeView(viewsets.ReadOnlyModelViewSet):
    queryset = TvEpisode.objects.all()
    serializer_class = TvEpisodeSerializer
    filterset_fields = ['season']

    @action(methods=['post'], detail=True)
    def download(self, request, pk=None):
        episode: TvEpisode = self.get_object()
        form = DownloadForm(request.POST)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
        url = form.cleaned_data['url']
        if episode.download_by_url(url):
            return Response('Ok')
        else:
            return Response('Invalid download', status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['delete'], detail=True)
    def remove(self, request, pk=None):
        episode: TvEpisode = self.get_object()
        if episode.status == TvEpisode.Status.READY:
            episode.set_path('')
            episode.save()
        return Response('Ok')