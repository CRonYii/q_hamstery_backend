from rest_framework import serializers
from .models import TorznabIndexer

class TorznabIndexerSerializer(serializers.ModelSerializer):
    class Meta:
        model = TorznabIndexer
        fields = ('id', 'name', 'url', 'apikey')