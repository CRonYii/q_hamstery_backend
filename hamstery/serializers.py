from rest_framework import serializers
from .models import TorznabIndexer, TvLibrary, TvStorage

class TorznabIndexerSerializer(serializers.ModelSerializer):
    class Meta:
        model = TorznabIndexer
        fields = ('name', 'url', 'apikey')

class TvStorageSerializer(serializers.ModelSerializer):
    shows = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    class Meta:
        model = TvStorage
        fields = ('lib', 'path', 'shows')

class TvLibrarySerializer(serializers.ModelSerializer):
    class Meta:
        model = TvLibrary        
        fields = ('name', 'lang', 'storages')