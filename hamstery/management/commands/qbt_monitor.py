import logging

from django.core.management.base import BaseCommand

from hamstery import qbt_monitor

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run qbittorrent monitor'

    def handle(self, *args, **options):
        qbt_monitor.start()