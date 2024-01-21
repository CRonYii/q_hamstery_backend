import logging
import traceback
from typing import List

import requests
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from hamstery.models import Indexer, TvEpisode, TvSeason
from hamstery.hamstery_settings import settings_manager
from hamstery.qbittorrent import qbt

logger = logging.getLogger(__name__)

# Create your models here.


class ShowSubscription(models.Model):
    season = models.ForeignKey(
        TvSeason, related_name='subs', on_delete=models.CASCADE, parent_link=True)
    indexer = models.ForeignKey(
        Indexer, related_name='subs', on_delete=models.CASCADE, parent_link=True)
    query = models.CharField(max_length=1024)
    # the smaller the more prioritized
    priority = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    # Used when the episode counts includes previous seasons
    offset = models.IntegerField(
        blank=True, default=0)
    exclude = models.CharField(max_length=512, blank=True, default='')
    done = models.BooleanField(default=False)

    def monitor_step(self):
        if self.check_done() is True:
            self.done = True
            self.save()
            return
        from hamstery.models import MonitoredTvDownload
        self.season.scan()
        results = self.season.search_episodes_from_indexer(
            self.query, self.indexer, self.offset, self.exclude)
        self.season.show.storage.lib  # pre-fetch lib here
        episodes: List[TvEpisode] = self.season.episodes.all()
        for ep in episodes:
            torrents = results[ep.episode_number]
            if len(torrents) == 0:
                continue
            if ep.status == TvEpisode.Status.READY:
                # If episode already exist, checks if the episode is downloaded by a subscriotion
                downloads = MonitoredTvDownload.objects.filter(
                    episode=ep, done=True)
                if len(downloads) == 0:
                    # Skip since episode is downloaded/imported by user
                    continue
                if downloads[0].subscription.priority <= self.priority:
                    # Skip since download has equal or higher priority
                    continue
            # We only download the first matched torrent
            torrent = torrents[0]
            try:
                if 'magneturl' in torrent:
                    ep.monitor_download_by_url(self.id, torrent['magneturl'])
                elif torrent['link'].startswith('magnet:'):
                    ep.monitor_download_by_url(self.id, torrent['link'])
                else:
                    r = requests.get(torrent['link'])
                    ep.monitor_download_by_torrents(self.id, r.content)
            except Exception:
                logger.error('Failed to download monitored-tv (%s): %s' % (torrent['title'], traceback.format_exc()))
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
            downloads = MonitoredTvDownload.objects.filter(
                episode=ep, done=True)
            if len(downloads) == 0:
                continue
            if downloads[0].subscription.priority > self.priority:
                # current downldoad has a lower priority
                return False
        return True

    def __str__(self):
        return self.query


def show_subscription_monitor_step():
    settings_manager.manual_update()
    if qbt.known_status is False:
        return
    logger.info('Show subscriptions monitor triggered')
    subs = ShowSubscription.objects.filter(done=False)
    for sub in subs:
        sub.monitor_step()


@receiver(pre_delete, sender=ShowSubscription, dispatch_uid='show_subscription_delete_signal')
def show_subscription_pre_delete(sender, instance: ShowSubscription, using, **kwargs):
    for download in instance.downloads.all():
        download.delete(keep_parents=True)
