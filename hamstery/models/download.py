from django.db import models
import logging

from hamstery.models.library import TvEpisode
from hamstery.models.show_subscription import ShowSubscription

logger = logging.getLogger(__name__)

# Create your models here.

class Download(models.Model):
    hash = models.CharField(max_length=256, primary_key=True)
    done = models.BooleanField(default=False)

    class Meta:
        abstract = True


class TvDownload(Download):
    episode: TvEpisode = models.ForeignKey(
        TvEpisode, related_name='downloads', on_delete=models.CASCADE, parent_link=True)
    filename = models.CharField(max_length=4096, blank=True, default='')

    def cancel(self):
        from ..qbittorrent import qbt
        qbt.client.torrents_delete(True, self.hash)
        self.delete()

class MonitoredTvDownload(TvDownload):
    subscription = models.ForeignKey(
        ShowSubscription, related_name='downloads', on_delete=models.DO_NOTHING, parent_link=True)
