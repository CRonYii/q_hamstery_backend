import logging
from django.utils import timezone

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from hamstery.models.show_subscrition import show_subscription_monitor_step
from hamstery.qbittorrent import qbt
from hamstery import utils

logger = logging.getLogger(__name__)

scheduler = BlockingScheduler(timezone=str(utils.tz))


def schedule_show_subscription_monitor_job():
    qbt.auto_test = True
    qbt.test_connection()
    job = scheduler.add_job(show_subscription_monitor_step,
                            trigger=IntervalTrigger(seconds=3600),
                            id="show_subscription_monitor",
                            max_instances=1,
                            )
    job.modify(next_run_time=utils.now())
    logger.info("Started show subscription monitor")
    return True


def start():
    if schedule_show_subscription_monitor_job():
        scheduler.start()


if __name__ == '__main__':
    start()
