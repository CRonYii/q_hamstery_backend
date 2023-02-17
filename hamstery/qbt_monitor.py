import logging

import qbittorrentapi
import tzlocal
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from hamstery.qbittorrent import qbittorrent_monitor_step, qbt_client

logger = logging.getLogger(__name__)

scheduler = BlockingScheduler(timezone=str(tzlocal.get_localzone()))

def schedule_qbittorrent_job():
    try:
        qbt_client.auth_log_in()
        # display qBittorrent info
        # require Web API >= 2.8.3 to run properly
        logger.info(f'qBittorrent: {qbt_client.app.version}')
        logger.info(
            f'qBittorrent Web API: {qbt_client.app.web_api_version}')
    except qbittorrentapi.LoginFailed as e:
        logger.error(e)
        return False
    scheduler.add_job(qbittorrent_monitor_step,
                      trigger=IntervalTrigger(seconds=1),
                      id="qbt_monitor",
                      max_instances=1,
                      )
    logger.info("Started qbittorrent monitor")
    return True


def start():
    if schedule_qbittorrent_job():
        scheduler.start()

if __name__ == '__main__':
    start()