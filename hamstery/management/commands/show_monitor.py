import logging

from django.core.management.base import BaseCommand

from hamstery import show_monitor

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run show subscription monitor'

    def handle(self, *args, **options):
        show_monitor.start()