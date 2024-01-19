import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from hamstery.models.settings import HamsterySettings

logger = logging.getLogger(__name__)


class SettingsHandler:

    def __init__(self, fields, action):
        self.fields = fields
        self.action = action

    def should_handle(self, old: HamsterySettings, new: HamsterySettings):
        for field in self.fields:
            if getattr(old, field, '') != getattr(new, field, ''):
                return True
        return False

    def update(self, old: HamsterySettings, new: HamsterySettings):
        if not self.should_handle(old, new):
            return
        self.action(new)


class HamsterySettingsManager:

    def __init__(self):
        if settings.BUILDING is False:
            # create a default singleton if not existed yet
            self.settings = HamsterySettings.singleton()
        else:
            self.settings = None
        self.handlers = []

    def register_settings_handler(self, handler: SettingsHandler):
        self.handlers.append(handler)

    def update(self, instance: HamsterySettings):
        for handler in self.handlers:
            handler.update(self.settings, instance)
        # update to latest settings
        self.settings = instance

    def manual_update(self):
        self.update(HamsterySettings.singleton())


settings_manager = HamsterySettingsManager()


UWSGI_HAMSTERY_SETTINGS_UPDATE = 1

@receiver(post_save, sender=HamsterySettings, dispatch_uid='hamstery_settings_update_handler')
def hamstery_settings_post_save(sender, instance: HamsterySettings, **kwargs):
    try:
        import uwsgi
        uwsgi.signal(UWSGI_HAMSTERY_SETTINGS_UPDATE)
        logger.info('Dispatched uWSGI signal to update hamstery settings')
    except ImportError:
        settings_manager.update(instance)


def hamstery_settings_uwsgi_handler(num):
    settings_manager.manual_update()
    logger.info('Received uWSGI signal to update hamstery settings')
