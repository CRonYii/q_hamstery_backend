import logging
import os
import traceback
from typing import Any, Callable
from pathlib import Path

import qbittorrentapi
from django.conf import settings

from hamstery.models.download import TvDownload
from hamstery.models.library import TvEpisode
from hamstery.utils import Result, failure, is_video_extension, success

logger = logging.getLogger(__name__)

HAMSTERY_CATEGORY = "hamstery-download (%s)" % settings.HOST_NAME

UNSCHEDULED_TV_TAG = "unscheduled-tv"
FETCHING_TV_TAG = "fetching-tv"
DOWNLOADING_TV_TAG = "downloading-tv"
DOWNLOADED_TV_TAG = "downloaded-tv"
ORGANIZED_TV_TAG = "organized-tv"
ERROR_TV_TAG = "error-tv"

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
        try:
            r = handler(task)
            if r.success is False:
                # do not delete files if it's because download cannot be found in DB
                # This can happen in the event of upgrade bug/reinstallation of hamstery 
                # so DB data is lost but downlaod is still kept in qbittorrent
                in_db = r.data() != 'Cannot find download in DB'
                qbt_client.torrents_delete(in_db, task['hash'])
                if in_db:
                    TvDownload.objects.filter(pk=task['hash']).delete()
                logger.warning('%s Download "%s" cancelled: %s' % (tag, task['name'], r.data()))
            else:
                if r.data() is not None:
                    logger.info('%s Download "%s" move to next phase: %s' % (tag, task['name'], r.data()))
        except Exception:
            logger.error(traceback.format_exc())
            qbt_client.torrents_remove_tags(tag, task['hash'])
            qbt_client.torrents_add_tags(ERROR_TV_TAG, task['hash'])



def handle_unscheduled_tv_task(task):
    try:
        ep_id = int(task['name'])
        episode: TvEpisode = TvEpisode.objects.get(pk=ep_id)
    except (TvEpisode.DoesNotExist, ValueError):
        return failure('Cannot find download in DB')
    filename = episode.get_formatted_filename()
    
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
        return failure('Cannot find download in DB')
    files = qbt_client.torrents_files(hash)
    if len(files) == 0:
        # skip this time, torrents need some time to fecth content...
        return success(None)
    target_files = list(filter(lambda f: is_video_extension(f['name']), files))
    if len(target_files) == 0:
        return failure('No video file found in download')
    if len(target_files) > 1:
        return failure('Unsupported multi files torrent episode download')

    target_file = target_files[0]
    filename = target_file['name']

    download.filename = filename
    download.save()
    if len(files) != 1:
        # We only download the video file at this time
        do_not_download_files = map(lambda f: f['index'], filter(lambda f: f['index'] is not target_file['index'], files))
        qbt_client.torrents_file_priority(hash, do_not_download_files, priority=0)
    qbt_client.torrents_rename(hash, "%s (%s)" % (task['name'], filename))
    qbt_client.torrents_remove_tags(FETCHING_TV_TAG, hash)
    qbt_client.torrents_add_tags(DOWNLOADING_TV_TAG, hash)
    return success('Valid TV download')


def handle_fetching_tv_tasks():
    handle_tasks(FETCHING_TV_TAG, handle_fetching_tv_task)


def handle_completed_tv_task(task):
    try:
        hash = task['hash']
        download: TvDownload = TvDownload.objects.get(pk=hash)
    except (TvDownload.DoesNotExist, ValueError):
        return failure('Cannot find download in DB')
    episode: TvEpisode = download.episode
    
    download.done = True
    download.save()

    _, original_name, ext = download.get_name_and_ext()
    folder = episode.get_folder()
    filename = "%s (%s)%s" % (episode.get_formatted_filename(), original_name, ext)

    qbt_client.torrents_set_location(folder, hash)
    qbt_client.torrents_rename_file(hash, old_path=download.filename, new_path=filename)
    qbt_client.torrents_remove_tags(DOWNLOADING_TV_TAG, hash)
    qbt_client.torrents_add_tags(DOWNLOADED_TV_TAG, hash)

    return success('TV download completed')


def handle_downloading_tv_tasks():
    handle_tasks(DOWNLOADING_TV_TAG, handle_completed_tv_task, status='completed')


def handle_organized_tv_task(task):
    try:
        hash = task['hash']
        download: TvDownload = TvDownload.objects.get(pk=hash)
    except (TvDownload.DoesNotExist, ValueError):
        return failure('Cannot find download in DB')
    episode: TvEpisode = download.episode

    _, original_name, ext = download.get_name_and_ext()
    folder = episode.get_folder()
    filename = "%s (%s)%s" % (episode.get_formatted_filename(), original_name, ext)
    full_path = os.path.join(folder, filename)

    if not Path(full_path).exists():
        # Skip this time, qbittorent has not finished moving the file to final destination
        return success(None)
    episode.import_video(full_path)
    episode.save()
    qbt_client.torrents_remove_tags(DOWNLOADED_TV_TAG, hash)
    qbt_client.torrents_add_tags(ORGANIZED_TV_TAG, hash)
    
    return success('TV organized')


def handle_completed_tv_tasks():
    handle_tasks(DOWNLOADED_TV_TAG, handle_organized_tv_task)


def qbittorrent_handle_tv_downloads():
    handle_completed_tv_tasks()
    handle_downloading_tv_tasks()
    handle_fetching_tv_tasks()
    handle_unscheduled_tv_tasks()


def qbittorrent_monitor_step():
    qbittorrent_handle_tv_downloads()
    
