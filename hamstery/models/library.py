import asyncio
import errno
import logging
import os
import re
import shutil
import traceback
from datetime import datetime
from pathlib import Path
from typing import List, Sequence

from asgiref.sync import async_to_sync, sync_to_async
from django.db import models
from django.db.models import Q

from hamstery.models import Indexer
from hamstery.plex import plex_manager
from hamstery.tmdb import (tmdb_search_tv_shows, tmdb_tv_season_details,
                           tmdb_tv_show_details)
from hamstery.utils import (failure, get_episode_number_from_title,
                            get_valid_filename, list_supplemental_file,
                            is_video_extension, list_dir, success,
                            tree_media, validate_directory_exist, value_or)

logger = logging.getLogger(__name__)


class TvLibrary(models.Model):
    name = models.CharField(max_length=120)
    TMDB_LANG = [
        ('xx', 'No Language'), ('aa', 'Afar'), ('af', 'Afrikaans'), ('ak', 'Akan'), ('an', 'Aragonese'), ('as', 'Assamese'), ('av', 'Avaric'), ('ae', 'Avestan'), ('ay', 'Aymara'), ('az', 'Azərbaycan'), ('ba', 'Bashkir'), ('bm', 'Bamanankan'), ('bi', 'Bislama'), ('bo', 'Tibetan'), ('br', 'Breton'), ('ca', 'Català'), ('cs', 'Český'), ('ce', 'Chechen'), ('cu', 'Slavic'), ('cv', 'Chuvash'), ('kw', 'Cornish'), ('co', 'Corsican'), ('cr', 'Cree'), ('cy', 'Cymraeg'), ('da', 'Dansk'), ('de', 'Deutsch'), ('dv', 'Divehi'), ('dz', 'Dzongkha'), ('eo', 'Esperanto'), ('et', 'Eesti'), ('eu', 'euskera'), ('fo', 'Faroese'), ('fj', 'Fijian'), ('fi', 'suomi'), ('fr', 'Français'), ('fy', 'Frisian'), ('ff', 'Fulfulde'), ('gd', 'Gaelic'), ('ga', 'Gaeilge'), ('gl', 'Galego'), ('gv', 'Manx'), ('gn', 'Guarani'), ('gu', 'Gujarati'), ('ht', 'Haitian; Haitian Creole'), ('ha', 'Hausa'), ('sh', 'Serbo-Croatian'), ('hz', 'Herero'), ('ho', 'Hiri Motu'), ('hr', 'Hrvatski'), ('hu', 'Magyar'), ('ig', 'Igbo'), ('io', 'Ido'), ('ii', 'Yi'), ('iu', 'Inuktitut'), ('ie', 'Interlingue'), ('ia', 'Interlingua'), ('id', 'Bahasa indonesia'), ('ik', 'Inupiaq'), ('is', 'Íslenska'), ('it', 'Italiano'), ('jv', 'Javanese'), ('ja', '日本語'), ('kl', 'Kalaallisut'), ('kn', 'Kannada'), ('ks', 'Kashmiri'), ('kr', 'Kanuri'), ('kk', 'қазақ'), ('km', 'Khmer'), ('ki', 'Kikuyu'), ('rw', 'Kinyarwanda'), ('ky', 'Kirghiz'), ('kv', 'Komi'), ('kg', 'Kongo'), ('ko', '한국어/조선말'), ('kj', 'Kuanyama'), ('ku', 'Kurdish'), ('lo', 'Lao'), ('la', 'Latin'), ('lv', 'Latviešu'), ('li', 'Limburgish'), ('ln', 'Lingala'), ('lt', 'Lietuvių'), ('lb', 'Letzeburgesch'), ('lu', 'Luba-Katanga'), ('lg', 'Ganda'), ('mh', 'Marshall'), ('ml', 'Malayalam'), ('mr', 'Marathi'), ('mg', 'Malagasy'), ('mt', 'Malti'), ('mo', 'Moldavian'), ('mn', 'Mongolian'), ('mi', 'Maori'), ('ms',
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                'Bahasa melayu'), ('my', 'Burmese'), ('na', 'Nauru'), ('nv', 'Navajo'), ('nr', 'Ndebele'), ('nd', 'Ndebele'), ('ng', 'Ndonga'), ('ne', 'Nepali'), ('nl', 'Nederlands'), ('nn', 'Norwegian Nynorsk'), ('nb', 'Bokmål'), ('no', 'Norsk'), ('ny', 'Chichewa; Nyanja'), ('oc', 'Occitan'), ('oj', 'Ojibwa'), ('or', 'Oriya'), ('om', 'Oromo'), ('os', 'Ossetian; Ossetic'), ('pi', 'Pali'), ('pl', 'Polski'), ('pt', 'Português'), ('qu', 'Quechua'), ('rm', 'Raeto-Romance'), ('ro', 'Română'), ('rn', 'Kirundi'), ('ru', 'Pусский'), ('sg', 'Sango'), ('sa', 'Sanskrit'), ('si', 'සිංහල'), ('sk', 'Slovenčina'), ('sl', 'Slovenščina'), ('se', 'Northern Sami'), ('sm', 'Samoan'), ('sn', 'Shona'), ('sd', 'Sindhi'), ('so', 'Somali'), ('st', 'Sotho'), ('es', 'Español'), ('sq', 'shqip'), ('sc', 'Sardinian'), ('sr', 'Srpski'), ('ss', 'Swati'), ('su', 'Sundanese'), ('sw', 'Kiswahili'), ('sv', 'svenska'), ('ty', 'Tahitian'), ('ta', 'தமிழ்'), ('tt', 'Tatar'), ('te', 'తెలుగు'), ('tg', 'Tajik'), ('tl', 'Tagalog'), ('th', 'ภาษาไทย'), ('ti', 'Tigrinya'), ('to', 'Tonga'), ('tn', 'Tswana'), ('ts', 'Tsonga'), ('tk', 'Turkmen'), ('tr', 'Türkçe'), ('tw', 'Twi'), ('ug', 'Uighur'), ('uk', 'Український'), ('ur', 'اردو'), ('uz', 'ozbek'), ('ve', 'Venda'), ('vi', 'Tiếng Việt'), ('vo', 'Volapük'), ('wa', 'Walloon'), ('wo', 'Wolof'), ('xh', 'Xhosa'), ('yi', 'Yiddish'), ('za', 'Zhuang'), ('zu', 'isiZulu'), ('ab', 'Abkhazian'), ('zh', '普通话'), ('ps', 'پښتو'), ('am', 'Amharic'), ('ar', 'العربية'), ('bg', 'български език'), ('cn', '广州话 / 廣州話'), ('mk', 'Macedonian'), ('el', 'ελληνικά'), ('fa', 'فارسی'), ('he', 'עִבְרִית'), ('hi', 'हिन्दी'), ('hy', 'Armenian'), ('en', 'English'), ('ee', 'Èʋegbe'), ('ka', 'ქართული'), ('pa', 'ਪੰਜਾਬੀ'), ('bn', 'বাংলা'), ('bs', 'Bosanski'), ('ch', 'Finu\' Chamorro'), ('be', 'беларуская мова'), ('yo', 'Èdè Yorùbá')
    ]
    lang = models.CharField(max_length=2, choices=TMDB_LANG, default='xx')

    @async_to_sync
    async def scan(self):
        res = success()
        storages: Sequence[TvStorage] = self.storages.all()
        routines = []
        async for storage in storages:
            routines.append(storage.scan())
        results = await asyncio.gather(*routines)
        for r in results:
            res = res.agg(r)
        return res

    def __str__(self):
        return self.name


class TvStorage(models.Model):
    lib = models.ForeignKey(
        TvLibrary, related_name='storages', on_delete=models.CASCADE, parent_link=True)
    path = models.CharField(max_length=4096, validators=[
                            validate_directory_exist])
    scanning = models.BooleanField(default=False)

    async def scan(self):
        if self.scanning is True:
            return success()
        res = success(self.id)
        self.scanning = True
        await sync_to_async(self.save)()
        try:
            logger.info('scanning storage %s' % self.path)
            async for show in self.shows.all():
                if not os.path.isdir(show.path):
                    await sync_to_async(show.delete)()
            routines = []
            for (dirpath, dir) in list_dir(self.path):
                try:
                    routines.append(
                        TvShow.objects.scan_for_show(self, dirpath, dir))
                except Exception as e:
                    logger.error(traceback.format_exc())
                    res.agg(failure('Failed to scan show directory %s: %s' %
                            (os.path.join(dirpath, dir), str(e))))
            await asyncio.gather(*routines)
        except Exception as e:
            logger.error(traceback.format_exc())
            res.agg(failure('Failed to scan storage %s: %s' %
                    (self.path, str(e))))
        finally:
            self.scanning = False
            await sync_to_async(self.save)()
            return res

    def __str__(self):
        return self.path


class TvShowManager(models.Manager):
    SEASON_FOLDER_RE = re.compile(r'(?i:season)\s+(\d{1,2})')

    async def create_or_update_by_tmdb_id(self, storage: TvStorage, tmdb_id, dirpath=''):
        logger.info('find metadata for show %s' % (dirpath))
        res = await tmdb_tv_show_details(tmdb_id, lang=storage.lib.lang)
        if not res.success:
            return res
        details = res.data()
        name = details['name']
        air_date = value_or(details, 'first_air_date', '')
        air_date_year = None
        if air_date != '':
            air_datetime = datetime.strptime(air_date, '%Y-%m-%d')
            air_date_year = air_datetime.year
        else:
            air_date = None
        number_of_episodes = details['number_of_episodes']
        number_of_seasons = details['number_of_seasons']
        poster_path = value_or(details, 'poster_path', '')
        logger.info('scan show %s' % (name))
        try:
            # update
            show: TvShow = await storage.shows.aget(path=dirpath)
            show.name = name
            show.number_of_episodes = number_of_episodes
            show.number_of_seasons = number_of_seasons
            show.poster_path = poster_path
            show.air_date = air_date
        except TvShow.DoesNotExist:
            # or create
            if dirpath == '':
                show_name = get_valid_filename(name)
                if air_date_year is not None:
                    show_name = show_name + ' (%d)' % (air_date_year)
                dirpath = os.path.join(
                    storage.path, show_name)
                if not os.path.exists(dirpath):
                    os.mkdir(dirpath)
            show = TvShow(
                storage=storage,
                tmdb_id=tmdb_id,
                path=dirpath,
                name=name,
                number_of_episodes=number_of_episodes,
                number_of_seasons=number_of_seasons,
                poster_path=poster_path,
                air_date=air_date
            )
        await sync_to_async(show.save)()
        logger.info('saved show %s' % (name))
        seasons = details['seasons']
        await show.scan_seasons(seasons)

    TITLE_YEAR_REGEX = re.compile(r'(.*?)\s*\((\d{4})\)?')

    @staticmethod
    def get_title_and_year(name):
        match = TvShowManager.TITLE_YEAR_REGEX.search(name)
        if match:
            return [match.group(1), match.group(2)]
        else:
            return [name, '']

    async def scan_for_show(self, storage: TvStorage, dirpath, dir):
        logger.info('search for show %s - %s' % (dirpath, dir))
        # Find the best matched tv show via tmdb
        [name, year] = TvShowManager.get_title_and_year(dir)
        tmdb_res = await tmdb_search_tv_shows(
            query=name, lang=storage.lib.lang, year=year)
        if not tmdb_res.success:
            return tmdb_res
        shows = tmdb_res.data()
        if shows['total_results'] == 0:
            return failure('Not found in TMDB')
        show_data = shows['results'][0]
        tmdb_id = show_data['id']
        await TvShow.objects.create_or_update_by_tmdb_id(
            storage, tmdb_id, os.path.join(dirpath, dir))
        return success('Ok')


class TvShow(models.Model):
    storage = models.ForeignKey(
        TvStorage, related_name='shows', on_delete=models.CASCADE, parent_link=True)
    tmdb_id = models.IntegerField()
    name = models.CharField(max_length=256)
    path = models.CharField(max_length=4096, db_index=True)
    number_of_episodes = models.IntegerField()
    number_of_seasons = models.IntegerField()
    poster_path = models.CharField(max_length=1024, blank=True, default='')
    air_date = models.DateField(blank=True, null=True)

    objects: TvShowManager = TvShowManager()

    def get_season_to_dir_map(self):
        season_map = dict()
        for (path, dir) in list_dir(self.path):
            fullpath = os.path.join(path, dir)
            if 'specials' in dir.lower():
                season_map[0] = fullpath
            else:
                match = TvShowManager.SEASON_FOLDER_RE.search(dir)
                if match:
                    season_number = int(match.group(1))
                    season_map[season_number] = fullpath
        return season_map

    @async_to_sync
    async def scan(self):
        res = success()
        try:
            await TvShow.objects.create_or_update_by_tmdb_id(self.storage, self.tmdb_id, self.path)
        except Exception as e:
            logger.error(traceback.format_exc())
            res.agg(failure('Failed to scan show %s: %s' %
                    (self.path, str(e))))
        return res

    async def scan_seasons(self, seasons):
        # clear removed seasons
        async for season in self.seasons.all():
            if not os.path.isdir(season.path):
                await sync_to_async(season.delete)()
        # scan seasons based on show's dir tree
        season_map = self.get_season_to_dir_map()
        routines = []
        for season in seasons:
            season_number = season['season_number']
            path = season_map.get(season_number, '')
            routines.append(TvSeason.objects.create_or_update_by_tmdb_id(
                self, self.tmdb_id, season_number, path))
        await asyncio.gather(*routines)

    def __str__(self):
        return self.name


class TvSeasonManager(models.Manager):
    async def create_or_update_by_tmdb_id(self, show: TvShow, tv_tmdb_id, season_number, dirpath=''):
        res = await tmdb_tv_season_details(
            tv_tmdb_id, season_number, lang=show.storage.lib.lang)
        if not res.success:
            return res
        details: dict = res.data()
        name = details['name']
        tmdb_id = details['id']
        episodes = details['episodes']
        number_of_episodes = len(episodes)
        poster_path = value_or(details, 'poster_path', show.poster_path)
        air_date = value_or(details, 'air_date', '')
        if air_date == '':
            air_date = None
        logger.info('scan season %s - Season %02d' %
                    (show.name, season_number))
        try:
            # update
            # should allow one entry per season per show.
            season: TvSeason = await show.seasons.aget(tmdb_id=tmdb_id)
            season.name = name
            season.number_of_episodes = number_of_episodes
            season.poster_path = poster_path
            season.air_date = air_date
            season.path = dirpath
        except TvSeason.DoesNotExist:
            # or create
            if dirpath == '':
                season_name = 'Season %d' % season_number
                if season_number == 0:
                    season_name = 'Specials'
                dirpath = os.path.join(
                    show.path, season_name)
                os.mkdir(dirpath)
            season = TvSeason(
                show=show,
                tmdb_id=tmdb_id,
                name=name,
                path=dirpath,
                season_number=season_number,
                number_of_episodes=number_of_episodes,
                poster_path=poster_path,
                air_date=air_date,
            )
        await sync_to_async(season.save)()
        await season.scan_episodes(episodes)


class TvSeason(models.Model):
    show = models.ForeignKey(
        TvShow, related_name='seasons', on_delete=models.CASCADE, parent_link=True)
    tmdb_id = models.IntegerField()
    name = models.CharField(max_length=256)
    path = models.CharField(max_length=4096, db_index=True)
    season_number = models.IntegerField()
    number_of_episodes = models.IntegerField()
    poster_path = models.CharField(max_length=1024, blank=True, default='')
    air_date = models.DateField(blank=True, null=True)

    objects: TvSeasonManager = TvSeasonManager()

    def get_episode_to_dir_map(self):
        episode_map = dict()
        for (path, filename) in tree_media(self.path)['files']:
            if not is_video_extension(filename):
                continue
            fullpath = os.path.join(path, filename)
            episode_number = get_episode_number_from_title(filename)
            if episode_number:
                episode_map[episode_number] = fullpath
        return episode_map

    @async_to_sync
    async def scan(self):
        res = success()
        try:
            tmdb_res = await tmdb_tv_season_details(self.show.tmdb_id, self.season_number, lang=self.show.storage.lib.lang)
            if not tmdb_res.success:
                return tmdb_res
            details = tmdb_res.data()
            episodes = details['episodes']
            logger.info('scan season %s - Season %02d' %
                        (self.show.name, self.season_number))
            await self.scan_episodes(episodes)
        except Exception as e:
            logger.error(traceback.format_exc())
            res.agg(failure('Failed to scan season %s: %s' %
                    (self.path, str(e))))
        return res

    async def scan_episodes(self, episodes):
        # We should not need to worry about clearing episodes unless # of episodes is reduced (which is unlikely)
        episode_map = self.get_episode_to_dir_map()
        ep_number_set = set()
        async for ep in self.episodes.all():
            ep_number_set.add(ep.episode_number)
        for episode in episodes:
            episode_number = episode['episode_number']
            path = episode_map.get(episode_number, '')
            await TvEpisode.objects.create_or_update_by_episode_number(season=self, details=episode, dirpath=path)
            if episode_number in ep_number_set:
                ep_number_set.remove(episode_number)
        for ep_n in ep_number_set:
            async for ep in self.episodes.filter(episode_number=ep_n):
                await sync_to_async(ep.delete)()

    def search_episodes_from_indexer(self, query: str, indexer: Indexer, offset=0, exclude=''):
        eps: List[TvEpisode] = self.episodes.all()
        exclude_re = None
        if exclude != '':
            exclude_re = re.compile(exclude)

        results = {}
        for ep in eps:
            adjusted_ep_n = ep.episode_number + offset
            if adjusted_ep_n <= 0:
                continue

            def filter_torrent(torrent):
                title = torrent['title']
                if exclude_re and exclude_re.search(title):
                    return False
                return get_episode_number_from_title(title) == adjusted_ep_n
            result = indexer.search(
                '%s %02d' % (query, adjusted_ep_n))
            if result.success != True:
                results[ep.episode_number] = []
                continue
            torrents = result.data()
            matched_torrents = list(filter(filter_torrent, torrents))
            results[ep.episode_number] = matched_torrents
        return results

    def __str__(self):
        return '%s - S%02d (%s)' % (self.show.name, self.season_number, self.name)


class TvEpisodeManager(models.Manager):
    async def create_or_update_by_episode_number(self, season: TvSeason, details, dirpath=''):
        episode_number = details['episode_number']
        tmdb_id = details['id']
        name = details['name']
        season_number = details['season_number']
        poster_path = value_or(details, 'still_path', season.poster_path)
        air_date = value_or(details, 'air_date', '')
        if air_date == '':
            air_date = None
        status = TvEpisode.Status.MISSING if dirpath == '' else TvEpisode.Status.READY

        try:
            # update
            episode: TvEpisode = await season.episodes.aget(episode_number=episode_number)
            episode.tmdb_id = tmdb_id
            episode.name = name
            episode.season_number = season_number
            episode.poster_path = poster_path
            episode.air_date = air_date
            await sync_to_async(episode.set_path)(dirpath)
        except TvEpisode.DoesNotExist:
            # or create
            episode = TvEpisode(
                season=season,
                tmdb_id=tmdb_id,
                status=status,
                name=name,
                path=dirpath,
                season_number=season_number,
                episode_number=episode_number,
                poster_path=poster_path,
                air_date=air_date,
            )
        await sync_to_async(episode.save)()


class TvEpisode(models.Model):
    season = models.ForeignKey(
        TvSeason, related_name='episodes', on_delete=models.CASCADE, parent_link=True)
    tmdb_id = models.IntegerField()

    class Status(models.IntegerChoices):
        MISSING = 1
        READY = 3
    status = models.IntegerField(choices=Status.choices)
    name = models.CharField(max_length=256)
    path = models.CharField(max_length=4096, blank=True, default='')
    season_number = models.IntegerField()
    episode_number = models.IntegerField(db_index=True)
    poster_path = models.CharField(max_length=1024, blank=True, default='')
    air_date = models.DateField(blank=True, null=True)

    objects: TvEpisodeManager = TvEpisodeManager()

    def set_path(self, path: str):
        if len(path) == 0:
            self.path = ''
            self.status = TvEpisode.Status.MISSING
            # It means the download has been removed externally, we will remove the download here as well.
            self.cancel_related_downloads('done')
        else:
            self.path = path
            self.status = TvEpisode.Status.READY

    def remove_episode(self):
        if self.status == TvEpisode.Status.MISSING:
            return True
        # Directly delete file on drive
        path = Path(self.path)
        if path.exists():
            try:
                os.remove(self.path)
            except OSError:
                # May be used by another process now, stop deletion
                return False
        for [p, f] in list_supplemental_file(self.path):
            sup_file = os.path.join(p, f)
            try:
                os.remove(sup_file)
            except:
                pass
        # delete all done downloads as well
        self.set_path('')
        # Update Plex
        plex_manager.refresh_plex_library_by_filepath(self.get_folder())
        return True

    def import_video(self, pathstr: str, manually: bool, mode='move') -> bool:
        path = Path(pathstr)
        season_folder = Path(self.get_folder())
        if not path.exists() or not path.is_file() or not is_video_extension(pathstr):
            logger.warn('Attempt to import invalid file: %s' % pathstr)
            return False
        if season_folder not in path.parents:
            def import_single_file(src, dst):
                if mode == 'symlink':
                    os.symlink(src, dst)
                elif mode == 'move':
                    shutil.move(src, dst)
                else:
                    os.link(src, dst)
            # Need to first move the file to season folder and rename
            src = pathstr
            names = [
                self.get_formatted_file_destination(src, 'full'),
                self.get_formatted_file_destination(src, 'meta_simple_original'),
                self.get_formatted_file_destination(src, 'meta_full'),
                self.get_formatted_file_destination(src, 'meta_simple'),
            ]
            done = False
            for name in names:
                pathstr = os.path.join(self.get_folder(), name)
                try:
                    import_single_file(src, pathstr)
                    done = True
                    break
                except OSError as e:
                    if e.errno == errno.ENAMETOOLONG:
                        continue
                    logger.error('Error when importing episode "%s" : %s' % (src, str(e)))
                    return False
            if done is False:
                logger.error('Error when importing episode "%s": All generated filename are too long' % src)
                return False
            # Move/rename subtitle files as well
            final_basename, _ = os.path.splitext(os.path.basename(pathstr))
            for [p, f] in list_supplemental_file(src):
                sup_file = os.path.join(p, f)
                _, sup_ext = f.split('.', maxsplit=1)
                try:
                    import_single_file(sup_file, os.path.join(self.get_folder(), "%s.%s" % (final_basename, sup_ext)))
                except OSError as e:
                    logger.warn('Error when importing supplemental file "%s": %s' % (sup_file, str(e)))
        self.path = pathstr
        self.status = TvEpisode.Status.READY
        if manually is True:
            self.cancel_related_downloads('downloading')
        plex_manager.refresh_plex_library_by_filepath(self.get_folder())
        return True

    def cancel_related_downloads(self, type: str):
        if type == 'all':
            downloads = self.downloads.all()
        elif type == 'downloading':
            downloads = self.downloads.filter(
                Q(monitoredtvdownload__isnull=False) | Q(done=False))
        elif type == 'done':
            downloads = self.downloads.filter(done=True)
        for download in downloads:
            logger.info('Deleted download "%s"' % download.filename)
            download.cancel()

    def get_formatted_file_destination(self, name, option='full'):
        _, video_filename = os.path.split(name)
        original_name, ext = os.path.splitext(video_filename)
        if option == 'meta_simple_original':
            return "%s (%s)%s" % (self.get_formatted_filename('simple'), original_name, ext)
        if option == 'meta_full':
            return "%s%s" % (self.get_formatted_filename(), ext)
        if option == 'meta_simple':
            return "%s%s" % (self.get_formatted_filename('simple'), ext)
        return "%s (%s)%s" % (self.get_formatted_filename(), original_name, ext)

    def get_formatted_filename(self, option='full'):
        season: TvSeason = self.season
        show: TvShow = season.show
        if option == 'simple':
            return "%s - S%02dE%02d" % (get_valid_filename(show.name), season.season_number, self.episode_number)
        return "%s - S%02dE%02d - %s" % (
            get_valid_filename(show.name), season.season_number, self.episode_number, get_valid_filename(self.name))

    def get_folder(self):
        season: TvSeason = self.season
        return season.path

    def is_manually_ready(self) -> bool:
        from hamstery.models import MonitoredTvDownload
        if self.status != TvEpisode.Status.READY:
            return False
        downloads = MonitoredTvDownload.objects.filter(episode=self, done=True)
        return len(downloads) == 0

    def download_by_url(self, urls):
        if self.is_manually_ready():
            return False
        from ..qbittorrent import (HAMSTERY_CATEGORY, UNSCHEDULED_TV_TAG,
                                   qbt)
        res = qbt.client.torrents_add(
            urls=urls,
            rename=self.id,
            category=HAMSTERY_CATEGORY,
            tags=UNSCHEDULED_TV_TAG,
            is_paused=False)
        if res == 'Ok.':
            return True
        else:
            return False

    def download_by_torrents(self, torrents):
        if self.is_manually_ready():
            return False
        from ..qbittorrent import (HAMSTERY_CATEGORY, UNSCHEDULED_TV_TAG,
                                   qbt)
        res = qbt.client.torrents_add(
            torrent_files=torrents,
            rename=self.id,
            category=HAMSTERY_CATEGORY,
            tags=UNSCHEDULED_TV_TAG,
            is_paused=False)
        if res == 'Ok.':
            return True
        else:
            return False

    def monitor_download_by_url(self, sub_id, urls):
        from ..qbittorrent import (HAMSTERY_CATEGORY, MONITORED_TV_TAG,
                                   UNSCHEDULED_TV_TAG, qbt)
        res = qbt.client.torrents_add(
            urls=urls,
            rename='%s,%s' % (self.id, sub_id),
            category=HAMSTERY_CATEGORY,
            tags=[UNSCHEDULED_TV_TAG, MONITORED_TV_TAG],
            is_paused=False)
        if res == 'Ok.':
            return True
        else:
            return False

    def monitor_download_by_torrents(self, sub_id, torrents):
        from ..qbittorrent import (HAMSTERY_CATEGORY, MONITORED_TV_TAG,
                                   UNSCHEDULED_TV_TAG, qbt)
        res = qbt.client.torrents_add(
            torrent_files=torrents,
            rename='%s,%s' % (self.id, sub_id),
            category=HAMSTERY_CATEGORY,
            tags=[UNSCHEDULED_TV_TAG, MONITORED_TV_TAG],
            is_paused=False)
        if res == 'Ok.':
            return True
        else:
            return False

    def __str__(self):
        return "%s - S%02dE%02d - %s" % (self.id, self.season_number, self.episode_number, self.name)
