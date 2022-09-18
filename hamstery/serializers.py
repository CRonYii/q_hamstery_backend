from rest_framework import serializers
from .models import TorznabIndexer, TvLibrary, TvStorage, TvShow, TvSeason, TvEpisode


class TorznabIndexerSerializer(serializers.ModelSerializer):
    class Meta:
        model = TorznabIndexer
        fields = ('id', 'name', 'url', 'apikey')


class TvEpisodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TvEpisode
        fields = ('id', 'season', 'tmdb_id', 'status', 'name', 'season_number',
                  'episode_number', 'poster_path', 'air_date')


class TvSeasonSerializer(serializers.ModelSerializer):
    episodes = TvEpisodeSerializer(many=True, read_only=True)

    class Meta:
        model = TvSeason
        fields = ('id', 'show', 'tmdb_id', 'name', 'season_number',
                  'number_of_episodes', 'poster_path', 'air_date', 'episodes')


class TvShowSerializer(serializers.ModelSerializer):
    seasons = TvSeasonSerializer(many=True, read_only=True)

    class Meta:
        model = TvShow
        fields = ('id', 'storage', 'tmdb_id', 'name', 'number_of_episodes',
                  'number_of_seasons', 'poster_path', 'air_date', 'seasons')


class EmbeddedTvShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = TvShow
        fields = ('id', 'tmdb_id', 'name', 'number_of_episodes',
                  'number_of_seasons', 'poster_path', 'air_date')


class TvStorageSerializer(serializers.ModelSerializer):
    shows = EmbeddedTvShowSerializer(many=True, read_only=True)

    class Meta:
        model = TvStorage
        fields = ('id', 'lib', 'path', 'shows')


class TvLibrarySerializer(serializers.ModelSerializer):
    storages = TvStorageSerializer(many=True, read_only=True)

    class Meta:
        model = TvLibrary
        fields = ('id', 'name', 'lang', 'storages')
