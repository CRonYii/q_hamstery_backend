from datetime import datetime
import logging

import qbittorrentapi
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from hamstery.models.show_subscrition import show_subscription_monitor_step
from hamstery.qbittorrent import qbittorrent_monitor_step, qbt_client

logger = logging.getLogger(__name__)


def qbt_start():
    try:
        qbt_client.auth_log_in()
        # display qBittorrent info
        logger.info(f'qBittorrent: {qbt_client.app.version}')
        logger.info(
            f'qBittorrent Web API: {qbt_client.app.web_api_version}')
    except qbittorrentapi.LoginFailed as e:
        logger.error(e)
        return False
    scheduler = BackgroundScheduler()
    scheduler.add_job(qbittorrent_monitor_step,
                      trigger=IntervalTrigger(seconds=1),
                      id="qbt_monitor",
                      max_instances=1,
                      )
    scheduler.start()
    logger.info("Started qbittorrent monitor")
    return True


def show_subscription_monitor_start():
    scheduler = BackgroundScheduler()
    job = scheduler.add_job(show_subscription_monitor_step,
                      trigger=IntervalTrigger(seconds=3600),
                      id="show_subscription_monitor",
                      max_instances=1,
                      )
    job.modify(next_run_time=datetime.now())
    scheduler.start()
    logger.info("Started show subscription monitor")


def start():
    qbt_start()
    show_subscription_monitor_start()
