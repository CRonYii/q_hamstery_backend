from django.apps import AppConfig


class HamsteryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hamstery'

    def ready(self) -> None:
        from django.conf import settings
        if settings.BUILDING is False:
            from . import background_scheduler
            background_scheduler.start()

