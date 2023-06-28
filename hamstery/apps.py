import logging

import tzlocal
from django.apps import AppConfig

logger = logging.getLogger(__name__)

class HamsteryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hamstery'

    def ready(self) -> None:
        logger.info('Timezone: %s' % (tzlocal.get_localzone()))
        try:
            import uwsgi
            from hamstery.hamstery_settings import hamstery_settings_uwsgi_handler, UWSGI_HAMSTERY_SETTINGS_UPDATE
            logger.info('Registered uWSGI signal handlers')
            uwsgi.register_signal(UWSGI_HAMSTERY_SETTINGS_UPDATE, "workers",
                            hamstery_settings_uwsgi_handler)
        except ImportError as e:
            print(str(e))
