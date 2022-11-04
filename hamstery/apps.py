from django.apps import AppConfig


class HamsteryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hamstery'

    def ready(self) -> None:
        from . import qbt_monitor
        qbt_monitor.start()