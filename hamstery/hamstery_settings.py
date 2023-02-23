import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from hamstery.models.settings import HamsterySettings

class SettingsHandler:

    def __init__(self, fields, action):
        self.fields = fields
        self.action = action

    def should_handle(self, old: HamsterySettings, new: HamsterySettings):
        for field in self.fields:
            if getattr(old, field) != getattr(new, field):
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

manager = HamsterySettingsManager()


@receiver(post_save, sender=HamsterySettings, dispatch_uid='hamstery_settings_update_handler')
def hamstery_settings_post_save(sender, instance: HamsterySettings, **kwargs):
    manager.update(instance)
