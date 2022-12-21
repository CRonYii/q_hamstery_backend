from typing import List
from django.db import models
import logging

from hamstery.models import TvEpisode, TvSeason, Indexer
from hamstery.utils import success

logger = logging.getLogger(__name__)

# Create your models here.

class ShowSubscription(models.Model):
    season = models.ForeignKey(
        TvSeason, related_name='subs', on_delete=models.CASCADE, parent_link=True)
    indexer = models.ForeignKey(
        Indexer, related_name='subs', on_delete=models.CASCADE, parent_link=True)
    query = models.CharField(max_length=1024)
    # the smaller the more prioritized
    priority = models.PositiveIntegerField()
    # Used when the episode counts includes previous seasons
    offset = models.PositiveIntegerField(blank=True, null=True)
    exclude = models.CharField(max_length=512, blank=True, default='')
    done = models.BooleanField(default=False)

    def monitor_step(self):
        self.done = self.check_done()
        if self.done:
            return
        from hamstery.models import MonitoredTvDownload
        results = self.season.search_episodes_from_indexer(self.query, self.indexer, self.offset, self.exclude)
        self.season.show.storage.lib # pre-fetch lib here
        self.season.scan()
        episodes: List[TvEpisode] = self.season.episodes.all()
        for ep in episodes:
            torrents = results[ep.episode_number]
            if len(torrents) == 0:
                continue
            if ep.status == TvEpisode.Status.READY:
                # If episode already exist, checks if the episode is downloaded by a subscriotion
                downloads = MonitoredTvDownload.objects.filter(episode=ep, done=True)
                if len(downloads) == 0:
                    # Skip since episode is downloaded/imported by user
                    continue
                if downloads[0].subscription.priority <= self.priority:
                    # Skip since download has equal or higher priority
                    continue
            # We only download the first matched torrent
            torrent = torrents[0]
            ep.monitor_download_by_url(self.id, torrent['link'])
        return

    def check_done(self):
        '''
        A subscription is considered done if all episodes are either
        1. downloaded/imported by user, or
        2. downloaded by a subscription with equal or higher priority
        '''
        from hamstery.models import MonitoredTvDownload
        episodes: List[TvEpisode] = self.season.episodes.all()
        for ep in episodes:
            if ep.status == TvEpisode.Status.MISSING:
                return False
            downloads = MonitoredTvDownload.objects.filter(episode=ep, done=True)
            if len(downloads) == 0:
                continue
            if downloads[0].subscription.priority > self.priority:
                # current downldoad has a lower priority
                return False
        return True

    def __str__(self):
        return self.query


def show_subscription_monitor_step():
    logger.info('show_subscription_monitor_step')
    subs = ShowSubscription.objects.filter(done=False)
    for sub in subs:
        sub.monitor_step()