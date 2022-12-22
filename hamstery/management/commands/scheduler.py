import logging

from django.core.management.base import BaseCommand

from hamstery import background_scheduler

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run Hamstery background scheduler'

    def handle(self, *args, **options):
        background_scheduler.start()