from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.schedulers.blocking import BlockingScheduler
import logging
import qbittorrentapi
from hamstery.qbittorrent import qbittorrent_monitor_step, qbt_client

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Monitor all hamstery related qbittorrent downloads'

    def handle(self, *args, **options):
        try:
            qbt_client.auth_log_in()
            # display qBittorrent info
            logger.info(f'qBittorrent: {qbt_client.app.version}')
            logger.info(
                f'qBittorrent Web API: {qbt_client.app.web_api_version}')
        except qbittorrentapi.LoginFailed as e:
            print(e)
            exit()
        scheduler = BlockingScheduler()
        scheduler.add_job(qbittorrent_monitor_step,
                          trigger=IntervalTrigger(seconds=1),
                          id="qbt_monitor",
                          max_instances=1,
                          )
        try:
            logger.info("Starting qbittorrent monitor...")
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Stopping qbittorrent monitor...")
            scheduler.shutdown()
            logger.info("qbittorrent monitor shut down successfully!")
