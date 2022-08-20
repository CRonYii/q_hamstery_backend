import aiohttp
import logging

from .utils import Result, failure, success

logger = logging.getLogger(__name__)

TMDB_API_KEY = 'e0c3646a54719a22df8b8e2c3f2e06ed'


async def tmdb_api_request(url, params) -> Result:
    try:
        params['api_key'] = TMDB_API_KEY
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                res = await response.json()
                if 'success' in res and res['success'] is False:
                    return failure(res['status_message'])
                return success(res)
    except aiohttp.ClientConnectionError as e:
        logger.warning(str(e))
        return failure(str(e))


def tmdb_search_tv_shows(query, lang=None, year=None):
    return tmdb_api_request('https://api.themoviedb.org/3/search/tv',
                            {'query': query, 'language': lang, 'first_air_date_year': year})


def tmdb_tv_show_details(id: int, lang=None):
    return tmdb_api_request('https://api.themoviedb.org/3/tv/%d' % id,
                            {'language': lang})


def tmdb_tv_season_details(id: int, season_number, lang=None):
    return tmdb_api_request('https://api.themoviedb.org/3/tv/%d/season/%d' % (id, season_number),
                            {'language': lang})
