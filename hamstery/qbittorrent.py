import logging
import os
from typing import Any, Callable
from django.conf import settings
import qbittorrentapi
from hamstery.models.download import TvDownload

from hamstery.models.library import TvEpisode
from hamstery.utils import Result, failure, is_video_extension, success

logger = logging.getLogger(__name__)

HAMSTERY_CATEGORY = "hamstery-download"

UNSCHEDULED_TV_TAG = "unscheduled-tv"
FETCHING_TV_TAG = "fetching-tv"
DOWNLOADING_TV_TAG = "downloading-tv"
ORGANIZED_TV_TAG = "organized-tv"

QBITTORRENT_CONFIG = getattr(settings, "QBITTORRENT_CONFIG", None)
if QBITTORRENT_CONFIG is None:
    raise ValueError('Please configure QBITTORRENT_CONFIG in django settings.')

qbt_client = qbittorrentapi.Client(
    host=QBITTORRENT_CONFIG['host'],
    port=QBITTORRENT_CONFIG['port'],
    username=QBITTORRENT_CONFIG['username'],
    password=QBITTORRENT_CONFIG['password'],
)


def handle_tasks(tag, handler: Callable[[Any], Result], status=None):
    tasks = qbt_client.torrents_info(
        status_filter=status, category=HAMSTERY_CATEGORY, tag=tag)
    for task in tasks:
        r = handler(task)
        if r.success is False:
            qbt_client.torrents_delete(True, task['hash'])
            TvDownload.objects.filter(pk=task['hash']).delete()
            logger.warning('%s Download "%s" cancelled: %s' % (tag, task['name'], r.payload))
        else:
            if r.payload is not None:
                logger.info('%s Download "%s" move to next phase: %s' % (tag, task['name'], r.payload))


def handle_unscheduled_tv_task(task):
    try:
        ep_id = int(task['name'])
        episode: TvEpisode = TvEpisode.objects.get(pk=ep_id)
    except (TvEpisode.DoesNotExist, ValueError):
        return failure('Invalid download')
    filename = episode.get_formatted_filename()
    if episode.status == TvEpisode.Status.READY:
        return failure('Episode "%s" already exists' % filename)
    
    download: TvDownload = TvDownload.objects.create(hash=task['hash'], episode=episode)
    download.save()
    qbt_client.torrents_rename(task['hash'], filename)
    qbt_client.torrents_remove_tags(UNSCHEDULED_TV_TAG, task['hash'])
    qbt_client.torrents_add_tags(FETCHING_TV_TAG, task['hash'])
    
    return success('"%s" Download scheduled' % filename)


def handle_unscheduled_tv_tasks():
    handle_tasks(UNSCHEDULED_TV_TAG, handle_unscheduled_tv_task)


def handle_fetching_tv_task(task):
    try:
        hash = task['hash']
        download: TvDownload = TvDownload.objects.get(pk=hash)
    except (TvDownload.DoesNotExist, ValueError):
        return failure('Invalid download')
    episode = download.episode
    if episode.status == TvEpisode.Status.READY:
        return failure('Episode already exists')
    files = qbt_client.torrents_files(hash)
    if len(files) == 0:
        # skip this time, torrents need some time to fecth content...
        return success(None)
    files = list(filter(lambda f: is_video_extension(f['name']), files))
    if len(files) == 0:
        return failure('No video file found in download')
    if len(files) > 1:
        return failure('Unsupported multi files torrent episode download')

    filename = files[0]['name']
    download.filename = filename
    download.save()
    qbt_client.torrents_rename(hash, "%s (%s)" % (task['name'], filename))
    qbt_client.torrents_remove_tags(FETCHING_TV_TAG, hash)
    qbt_client.torrents_add_tags(DOWNLOADING_TV_TAG, hash)
    return success('Valid TV download')


def handle_fetching_tv_tasks():
    handle_tasks(FETCHING_TV_TAG, handle_fetching_tv_task)


def handle_downloading_tv_task(task):
    try:
        hash = task['hash']
        download: TvDownload = TvDownload.objects.get(pk=hash)
    except (TvDownload.DoesNotExist, ValueError):
        return failure('Invalid download')
    episode = download.episode
    if episode.status == TvEpisode.Status.READY:
        return failure('Episode already exists')
    
    return success(None)

def handle_completed_tv_task(task):
    try:
        hash = task['hash']
        download: TvDownload = TvDownload.objects.get(pk=hash)
    except (TvDownload.DoesNotExist, ValueError):
        return failure('Invalid download')
    episode: TvEpisode = download.episode
    if episode.status == TvEpisode.Status.READY:
        return failure('Episode already exists')
    
    download.done = True
    download.save()

    _, ext = os.path.splitext(download.filename)
    folder = episode.get_folder()
    filename = "%s%s" % (episode.get_formatted_filename(), ext)
    full_path = os.path.join(folder, filename)

    qbt_client.torrents_set_location(folder, hash)
    qbt_client.torrents_rename_file(hash, old_path=download.filename, new_path=filename)
    if episode.set_path(full_path) is False:
        return failure('Failed to import episode')
    episode.save()
    qbt_client.torrents_remove_tags(DOWNLOADING_TV_TAG, hash)
    qbt_client.torrents_add_tags(ORGANIZED_TV_TAG, hash)
    
    return success('TV organized')


def handle_downloading_tv_tasks():
    handle_tasks(DOWNLOADING_TV_TAG, handle_downloading_tv_task, status='downloading')
    handle_tasks(DOWNLOADING_TV_TAG, handle_completed_tv_task, status='completed')


def handle_organized_tv_task(task):
    try:
        hash = task['hash']
        _: TvDownload = TvDownload.objects.get(pk=hash)
    except TvDownload.DoesNotExist:
        return failure('Download removed')
    
    return success(None)


def handle_organized_tv_tasks():
    handle_tasks(ORGANIZED_TV_TAG, handle_organized_tv_task)


def qbittorrent_handle_tv_downloads():
    handle_organized_tv_tasks()
    handle_downloading_tv_tasks()
    handle_fetching_tv_tasks()
    handle_unscheduled_tv_tasks()


def qbittorrent_monitor_step():
    qbittorrent_handle_tv_downloads()


def download_episode(episode: TvEpisode, urls):
    res = qbt_client.torrents_add(
        urls=urls,
        rename=episode.id,
        category=HAMSTERY_CATEGORY,
        tags=UNSCHEDULED_TV_TAG,
        is_paused=False)
    if res == 'Ok.':
        return True
    else:
        return False
    