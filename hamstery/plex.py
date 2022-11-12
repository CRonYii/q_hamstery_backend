import logging
import urllib.parse
from pathlib import Path

import requests
from django.conf import settings

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


class PlexManager:

    def __init__(self, url, token):
        self.url = url
        self.token = token
        self.enabled = len(self.url) != 0 and len(self.token) != 0

    def __request(self, url, params={}):
        params['X-Plex-Token'] = self.token
        param_list = []
        for k, v in params.items(): 
            v = urllib.parse.quote(v, safe='~@#$&()*!+=:;,?/\'')
            param_list.append('%s=%s' % (k, v))

        query_str = '&'.join(param_list)
        
        return requests.get('%s%s' % (self.url, url),
                            params=query_str,
                            headers={'Accept': 'application/json'})

    def __get_libraries(self):
        req = self.__request('/library/sections')
        if req.ok:
            return req.json()
        return None

    def __find_libraries_by_path(self, path: str):
        data = self.__get_libraries()
        if data is None:
            return
        libs = data['MediaContainer']['Directory'] or []
        return filter(any_library_has_path(path), libs)

    def __refresh(self, lib, path: str):
        req = self.__request('/library/sections/%s/refresh' %
                             (lib['key']), {'path': path})
        if req.ok:
            logger.info('Refreshed Plex library <%s> "%s"' %
                        (lib['title'], path))
        else:
            logger.warn('Failed to refresh Plex library <%s> "%s"' %
                        (lib['title'], path))

    def refresh_plex_library_by_filepath(self, filepath: str):
        if not self.enabled:
            return
        path = Path(filepath)
        if path.is_file():
            path = path.parent
        filepath = str(path.absolute())
        libs = self.__find_libraries_by_path(filepath)
        for lib in libs:
            self.__refresh(lib, filepath)


if PLEX_CONFIG is not None:
    plex_manager = PlexManager(PLEX_CONFIG['url'], PLEX_CONFIG['token'])
else:
    plex_manager = None
