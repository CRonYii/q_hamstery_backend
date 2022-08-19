from posixpath import dirname
from statistics import mode
from typing import Sequence
from django.db import models
import os
import re
from datetime import datetime

from ..tmdb import tmdb_search_tv_shows, tmdb_tv_season_details, tmdb_tv_show_details
from ..utils import failure, list_dir, success, validate_directory_exist, value_or


class TvLibrary(models.Model):
    name = models.CharField(max_length=120)
    TMDB_LANG = [
        ('xx', 'No Language'), ('aa', 'Afar'), ('af', 'Afrikaans'), ('ak', 'Akan'), ('an', 'Aragonese'), ('as', 'Assamese'), ('av', 'Avaric'), ('ae', 'Avestan'), ('ay', 'Aymara'), ('az', 'Azərbaycan'), ('ba', 'Bashkir'), ('bm', 'Bamanankan'), ('bi', 'Bislama'), ('bo', 'Tibetan'), ('br', 'Breton'), ('ca', 'Català'), ('cs', 'Český'), ('ce', 'Chechen'), ('cu', 'Slavic'), ('cv', 'Chuvash'), ('kw', 'Cornish'), ('co', 'Corsican'), ('cr', 'Cree'), ('cy', 'Cymraeg'), ('da', 'Dansk'), ('de', 'Deutsch'), ('dv', 'Divehi'), ('dz', 'Dzongkha'), ('eo', 'Esperanto'), ('et', 'Eesti'), ('eu', 'euskera'), ('fo', 'Faroese'), ('fj', 'Fijian'), ('fi', 'suomi'), ('fr', 'Français'), ('fy', 'Frisian'), ('ff', 'Fulfulde'), ('gd', 'Gaelic'), ('ga', 'Gaeilge'), ('gl', 'Galego'), ('gv', 'Manx'), ('gn', 'Guarani'), ('gu', 'Gujarati'), ('ht', 'Haitian; Haitian Creole'), ('ha', 'Hausa'), ('sh', 'Serbo-Croatian'), ('hz', 'Herero'), ('ho', 'Hiri Motu'), ('hr', 'Hrvatski'), ('hu', 'Magyar'), ('ig', 'Igbo'), ('io', 'Ido'), ('ii', 'Yi'), ('iu', 'Inuktitut'), ('ie', 'Interlingue'), ('ia', 'Interlingua'), ('id', 'Bahasa indonesia'), ('ik', 'Inupiaq'), ('is', 'Íslenska'), ('it', 'Italiano'), ('jv', 'Javanese'), ('ja', '日本語'), ('kl', 'Kalaallisut'), ('kn', 'Kannada'), ('ks', 'Kashmiri'), ('kr', 'Kanuri'), ('kk', 'қазақ'), ('km', 'Khmer'), ('ki', 'Kikuyu'), ('rw', 'Kinyarwanda'), ('ky', 'Kirghiz'), ('kv', 'Komi'), ('kg', 'Kongo'), ('ko', '한국어/조선말'), ('kj', 'Kuanyama'), ('ku', 'Kurdish'), ('lo', 'Lao'), ('la', 'Latin'), ('lv', 'Latviešu'), ('li', 'Limburgish'), ('ln', 'Lingala'), ('lt', 'Lietuvių'), ('lb', 'Letzeburgesch'), ('lu', 'Luba-Katanga'), ('lg', 'Ganda'), ('mh', 'Marshall'), ('ml', 'Malayalam'), ('mr', 'Marathi'), ('mg', 'Malagasy'), ('mt', 'Malti'), ('mo', 'Moldavian'), ('mn', 'Mongolian'), ('mi', 'Maori'), ('ms',
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                'Bahasa melayu'), ('my', 'Burmese'), ('na', 'Nauru'), ('nv', 'Navajo'), ('nr', 'Ndebele'), ('nd', 'Ndebele'), ('ng', 'Ndonga'), ('ne', 'Nepali'), ('nl', 'Nederlands'), ('nn', 'Norwegian Nynorsk'), ('nb', 'Bokmål'), ('no', 'Norsk'), ('ny', 'Chichewa; Nyanja'), ('oc', 'Occitan'), ('oj', 'Ojibwa'), ('or', 'Oriya'), ('om', 'Oromo'), ('os', 'Ossetian; Ossetic'), ('pi', 'Pali'), ('pl', 'Polski'), ('pt', 'Português'), ('qu', 'Quechua'), ('rm', 'Raeto-Romance'), ('ro', 'Română'), ('rn', 'Kirundi'), ('ru', 'Pусский'), ('sg', 'Sango'), ('sa', 'Sanskrit'), ('si', 'සිංහල'), ('sk', 'Slovenčina'), ('sl', 'Slovenščina'), ('se', 'Northern Sami'), ('sm', 'Samoan'), ('sn', 'Shona'), ('sd', 'Sindhi'), ('so', 'Somali'), ('st', 'Sotho'), ('es', 'Español'), ('sq', 'shqip'), ('sc', 'Sardinian'), ('sr', 'Srpski'), ('ss', 'Swati'), ('su', 'Sundanese'), ('sw', 'Kiswahili'), ('sv', 'svenska'), ('ty', 'Tahitian'), ('ta', 'தமிழ்'), ('tt', 'Tatar'), ('te', 'తెలుగు'), ('tg', 'Tajik'), ('tl', 'Tagalog'), ('th', 'ภาษาไทย'), ('ti', 'Tigrinya'), ('to', 'Tonga'), ('tn', 'Tswana'), ('ts', 'Tsonga'), ('tk', 'Turkmen'), ('tr', 'Türkçe'), ('tw', 'Twi'), ('ug', 'Uighur'), ('uk', 'Український'), ('ur', 'اردو'), ('uz', 'ozbek'), ('ve', 'Venda'), ('vi', 'Tiếng Việt'), ('vo', 'Volapük'), ('wa', 'Walloon'), ('wo', 'Wolof'), ('xh', 'Xhosa'), ('yi', 'Yiddish'), ('za', 'Zhuang'), ('zu', 'isiZulu'), ('ab', 'Abkhazian'), ('zh', '普通话'), ('ps', 'پښتو'), ('am', 'Amharic'), ('ar', 'العربية'), ('bg', 'български език'), ('cn', '广州话 / 廣州話'), ('mk', 'Macedonian'), ('el', 'ελληνικά'), ('fa', 'فارسی'), ('he', 'עִבְרִית'), ('hi', 'हिन्दी'), ('hy', 'Armenian'), ('en', 'English'), ('ee', 'Èʋegbe'), ('ka', 'ქართული'), ('pa', 'ਪੰਜਾਬੀ'), ('bn', 'বাংলা'), ('bs', 'Bosanski'), ('ch', 'Finu\' Chamorro'), ('be', 'беларуская мова'), ('yo', 'Èdè Yorùbá')
    ]
    lang = models.CharField(max_length=2, choices=TMDB_LANG, default='xx')

    def scan(self):
        res = success('Ok')
        storages: Sequence[TvStorage] = self.storages.all()
        for storage in storages:
            res.agg(storage.scan())
        return res

    def __str__(self):
        return self.name


class TvStorage(models.Model):
    lib = models.ForeignKey(
        TvLibrary, related_name='storages', on_delete=models.CASCADE, parent_link=True)
    path = models.CharField(max_length=4096, validators=[
                            validate_directory_exist])
    scanning = models.BooleanField(default=False)

    def scan(self):
        res = success('Ok')
        if self.scanning is True:
            return res
        self.scanning = True
        self.save()
        try:
            print('scan storage', self.path)
            for show in self.shows.all():
                if not os.path.isdir(show.path):
                    show.delete()
            for (dirpath, dir) in list_dir(self.path):
                try:
                    print('scan show', dirpath, dir)
                    # Find the best matched tv show via tmdb
                    [name, year] = TvShowManager.get_title_and_year(dir)
                    tmdb_res = tmdb_search_tv_shows(
                        query=name, lang=self.lib.lang, year=year)
                    if not tmdb_res.success:
                        res.agg(tmdb_res)
                    shows = tmdb_res.payload
                    if shows['total_results'] == 0:
                        continue
                    show_data = shows['results'][0]
                    tmdb_id = show_data['id']
                    TvShow.objects.create_or_update_by_tmdb_id(
                        self, tmdb_id, os.path.join(dirpath, dir))
                except Exception as e:
                    res.agg(failure('Failed to scan show directory %s: %s' %
                            (os.path.join(dirpath, dir), str(e))))
        except Exception as e:
            res.agg(failure('Failed to scan storage %s: %s' %
                    (self.path, str(e))))
        finally:
            self.scanning = False
            self.save()
            return res

    def __str__(self):
        return self.path


class TvShowManager(models.Manager):
    SEASON_FOLDER_RE = re.compile(r'(?i:season)\s+(\d{1,2})')

    def create_or_update_by_tmdb_id(self, storage: TvStorage, tmdb_id, dirpath=''):
        res = tmdb_tv_show_details(tmdb_id, lang=storage.lib.lang)
        if not res.success:
            return res
        details = res.payload
        name = details['name']
        air_date = details['first_air_date']
        air_date = datetime.strptime(air_date, '%Y-%m-%d')
        number_of_episodes = details['number_of_episodes']
        number_of_seasons = details['number_of_seasons']
        poster_path = value_or(details, 'poster_path', '')
        try:
            # update
            show: TvShow = storage.shows.get(path=dirpath)
            show.name = name
            show.number_of_episodes = number_of_episodes
            show.number_of_seasons = number_of_seasons
            show.poster_path = poster_path
        except TvShow.DoesNotExist:
            # or create
            if dirpath == '':
                dirpath = os.path.join(storage.path, '%s (%d)' % (name, air_date.year))
                os.mkdir(dirpath)
            show = TvShow(
                storage=storage,
                tmdb_id=tmdb_id,
                path=dirpath,
                name=name,
                number_of_episodes=number_of_episodes,
                number_of_seasons=number_of_seasons,
                poster_path=poster_path,
            )
        show.save()
        seasons = details['seasons']
        show.scan_seasons(seasons)
        

    TITLE_YEAR_REGEX = re.compile(r'(.*?)\s*\((\d{4})\)?')

    @staticmethod
    def get_title_and_year(name):
        match = TvShowManager.TITLE_YEAR_REGEX.search(name)
        if match:
            return [match.group(1), match.group(2)]
        else:
            return [name, None]


class TvShow(models.Model):
    storage = models.ForeignKey(
        TvStorage, related_name='shows', on_delete=models.CASCADE, parent_link=True)
    tmdb_id = models.IntegerField()
    name = models.CharField(max_length=256)
    path = models.CharField(max_length=4096, db_index=True)
    number_of_episodes = models.IntegerField()
    number_of_seasons = models.IntegerField()
    poster_path = models.CharField(max_length=1024, blank=True, default='')

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


    def scan_seasons(self, seasons):
        # clear removed seasons
        for season in self.seasons.all():
            if not os.path.isdir(season.path):
                    season.delete()
        # scan seasons based on show's dir tree
        season_map = self.get_season_to_dir_map()
        for season in seasons:
            season_number = season['season_number']
            path = season_map.get(season_number, '')
            TvSeason.objects.create_or_update_by_tmdb_id(
                self, self.tmdb_id, season_number, path)

    def __str__(self):
        return self.name


class TvSeasonManager(models.Manager):
    def create_or_update_by_tmdb_id(self, show: TvShow, tv_tmdb_id, season_number, dirpath=''):
        res = tmdb_tv_season_details(
            tv_tmdb_id, season_number, lang=show.storage.lib.lang)
        if not res.success:
            return res
        details: dict = res.payload
        name = details['name']
        tmdb_id = details['id']
        episodes = details['episodes']
        number_of_episodes = len(episodes)
        poster_path = value_or(details, 'poster_path', show.poster_path)
        air_date = value_or(details, 'air_date', '')
        try:
            # update
            season: TvSeason = show.seasons.get(path=dirpath)
            season.tmdb_id = tmdb_id
            season.name = name
            season.number_of_episodes = number_of_episodes
            season.poster_path = poster_path
            season.air_date = air_date
        except TvSeason.DoesNotExist:
            # or create
            if dirpath == '':
                dirpath = os.path.join(show.path, 'Season %d' % season_number)
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
        season.save()
        season.scan_episodes(episodes)


class TvSeason(models.Model):
    show = models.ForeignKey(
        TvShow, related_name='seasons', on_delete=models.CASCADE, parent_link=True)
    tmdb_id = models.IntegerField()
    name = models.CharField(max_length=256)
    path = models.CharField(max_length=4096, db_index=True)
    season_number = models.IntegerField()
    number_of_episodes = models.IntegerField()
    poster_path = models.CharField(max_length=1024, blank=True, default='')
    air_date = models.DateField(blank=True)

    objects: TvSeasonManager = TvSeasonManager()

    EPISODE_NAME_RE = r'(?i:s\d{1,2}e(\d{1,4})).*?(mp4|mkv|flv|avi|rmvb|m4p|m4v)$'

    def get_episode_to_dir_map(self):
        episode_map = dict()
        for (path, dir) in list_dir(self.path):
            fullpath = os.path.join(path, dir)
            match = TvSeason.EPISODE_NAME_RE.search(dir)
            if match:
                episode_number = int(match.group(1))
                episode_map[episode_number] = fullpath
        return episode_map


    def scan_episodes(self, episodes):
        # We should not need to worry about clearing episodes unless # of episodes is reduced (which is unlikely)
        episode_map = self.get_episode_to_dir_map()
        for episode in episodes:
            episode_number = episode['episode_number']
            path = episode_map.get(episode_number, '')
            TvEpisode.objects.create_or_update_by_episode_number(season=self, details=episode, dirpath=path)
            

class TvEpisodeManager(models.Manager):
    def create_or_update_by_episode_number(self, season: TvSeason, details, dirpath=''):
        episode_number = details['episode_number']
        tmdb_id = details['id']
        name = details['name']
        season_number = details['season_number']
        poster_path = value_or(details, 'still_path', season.poster_path)
        air_date = value_or(details, 'air_date', '')
        status = TvEpisode.Status.MISSING if dirpath == '' else TvEpisode.Status.READY

        try:
            # update
            episode: TvEpisode = season.episodes.get(episode_number=episode_number)
            episode.tmdb_id = tmdb_id
            episode.name = name
            episode.season_number = season_number
            episode.poster_path = poster_path
            episode.air_date = air_date
            if episode.status == TvEpisode.Status.DOWNLOADING:
                if status == TvEpisode.Status.READY:
                    # TODO cancel download
                    pass
                # DOWNLOADING and MISSING, do not change status here.
            else:
                episode.status = status
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
        episode.save()

class TvEpisode(models.Model):
    season = models.ForeignKey(
        TvSeason, related_name='episodes', on_delete=models.CASCADE, parent_link=True)
    tmdb_id = models.IntegerField()

    class Status(models.IntegerChoices):
        MISSING = 1
        DOWNLOADING = 2
        READY = 3
    status = models.IntegerField(choices=Status.choices)
    name = models.CharField(max_length=256)
    path = models.CharField(max_length=4096, blank=True, default='')
    season_number = models.IntegerField()
    episode_number = models.IntegerField(db_index=True)
    poster_path = models.CharField(max_length=1024, blank=True, default='')
    air_date = models.DateField(blank=True)

    objects: TvEpisodeManager = TvEpisodeManager()