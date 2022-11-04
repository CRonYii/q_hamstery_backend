from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import qbittorrentapi
from hamstery.qbittorrent import qbittorrent_monitor_step, qbt_client

logger = logging.getLogger(__name__)

def start():
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
