from django.db import models
import logging

from hamstery.models.library import TvEpisode

logger = logging.getLogger(__name__)

# Create your models here.

class Download(models.Model):
    hash = models.CharField(max_length=256, primary_key=True)

    class Meta:
        abstract = True


class TvDownload(Download):
    episode: TvEpisode = models.ForeignKey(
        TvEpisode, related_name='downloads', on_delete=models.CASCADE, parent_link=True)
    filename = models.CharField(max_length=4096, blank=True, default='')