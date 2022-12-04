from django.db import models
import logging
import os

from hamstery.models.library import TvEpisode

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
        from ..qbittorrent import qbt_client
        qbt_client.torrents_delete(True, self.hash)
        if self.done is True:
            self.episode.remove_episode()
            self.episode.save()
        self.delete()

    def get_name_and_ext(self):
        '''
        Example 1: if the download name is 'a/b/video.mp4'
        Returns ('a/b', 'video', '.mp4')
        Example 2: if the download name is 'video.mp4'
        Returns ('', 'video', '.mp4')
        '''
        possible_dir, video_filename = os.path.split(self.filename)
        original_name, ext = os.path.splitext(video_filename)
        return possible_dir, original_name, ext