import logging

from django.apps import AppConfig
from django.utils import timezone

from hamstery import utils

logger = logging.getLogger(__name__)

class HamsteryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hamstery'

    def ready(self) -> None:
        logger.info('Timezone: %s' % (utils.tz))
        logger.info('Starup Time: %s' % (utils.now().strftime('%Y-%m-%d %H:%M:%S')))
        from hamstery.hamstery_settings import settings_manager
        from hamstery.qbittorrent import qbt
        from hamstery.plex import plex_manager
        from hamstery.openai import openai_manager
        try:
            import uwsgi
            from hamstery.hamstery_settings import hamstery_settings_uwsgi_handler, UWSGI_HAMSTERY_SETTINGS_UPDATE
            logger.info('Registered uWSGI signal handlers')
            uwsgi.register_signal(UWSGI_HAMSTERY_SETTINGS_UPDATE, "workers",
                            hamstery_settings_uwsgi_handler)
        except ImportError as e:
            print(str(e))
