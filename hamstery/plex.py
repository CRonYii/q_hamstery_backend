import logging
import urllib.parse
from pathlib import Path

import requests
from django.conf import settings

from hamstery.hamstery_settings import SettingsHandler, manager
from hamstery.models.settings import HamsterySettings

from .utils import is_subdirectory

logger = logging.getLogger(__name__)
PLEX_CONFIG = getattr(settings, "PLEX_CONFIG", None)


def any_library_has_path(path):
    def f(lib):
        for loc in lib['Location']:
            if is_subdirectory(loc['path'], path):
                return True
        return False
    return f


class PlexClient:

    def __init__(self, url, token):
        self.url = url
        self.token = token
        self.enabled = len(self.url) != 0 and len(self.token) != 0

    def request(self, url, params={}):
        params['X-Plex-Token'] = self.token
        param_list = []
        for k, v in params.items():
            v = urllib.parse.quote(v, safe='~@#$&()*!+=:;,?/\'')
            param_list.append('%s=%s' % (k, v))

        query_str = '&'.join(param_list)

        return requests.get('%s%s' % (self.url, url),
                            params=query_str,
                            headers={'Accept': 'application/json'})

    def test_connection(self):
        try:
            req = self.request('/library/sections')
            if not req.ok:
                return [False, f'''Plex Server error {self.url} token={self.token}: {req.reason}''']
            return [True, f'''Successfully connected to Plex Server {self.url} token={self.token}''']
        except requests.exceptions.RequestException as e:
            return [False, f'''Failed to connect to Plex Server {self.url} token={self.token} with error: 
{e}''']

    def get_libraries(self):
        req = self.request('/library/sections')
        if req.ok:
            return req.json()
        return None

    def find_libraries_by_path(self, path: str):
        data = self.get_libraries()
        if data is None:
            return None
        libs = data['MediaContainer']['Directory'] or []
        return filter(any_library_has_path(path), libs)

    def refresh(self, lib, path: str):
        req = self.request('/library/sections/%s/refresh' %
                             (lib['key']), {'path': path})
        if req.ok:
            logger.info('Refreshed Plex library <%s> "%s"' %
                        (lib['title'], path))
        else:
            logger.warn('Failed to refresh Plex library <%s> "%s"' %
                        (lib['title'], path))


class PlexManager:

    client = None
    enable = False

    def __init__(self):
        if settings.BUILDING is True:
            return
        instance = HamsterySettings.singleton()
        self.load_client(instance)
        manager.register_settings_handler(SettingsHandler([
            'plex_enable',
            'plex_url',
            'plex_token',
        ], self.on_plex_config_update))

    def load_client(self, instance: HamsterySettings):
        self.enable = instance.plex_enable and (instance.plex_url != '' and instance.plex_token != '')
        self.client = PlexClient(instance.plex_url, instance.plex_token)

    def on_plex_config_update(self, instance: HamsterySettings):
        logger.info(
            'Detected Plex configuration changes, loading new Plex client...')
        self.load_client(instance)

    def refresh_plex_library_by_filepath(self, filepath: str) -> bool:
        if not self.enable:
            return True
        try:
            path = Path(filepath)
            if path.is_file():
                path = path.parent
            filepath = str(path.absolute())
            libs = self.client.find_libraries_by_path(filepath)
            if libs is None:
                return False
            for lib in libs:
                self.client.refresh(lib, filepath)
            return True
        except:
            return False

    def test_connection(self):
        if self.enable is False:
            return [False, 'Plex integration is not enabled']
        return self.client.test_connection()


plex_manager = PlexManager()
