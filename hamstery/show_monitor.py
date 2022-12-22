import logging
from datetime import datetime

import tzlocal
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from hamstery.models.show_subscrition import show_subscription_monitor_step

logger = logging.getLogger(__name__)

scheduler = BlockingScheduler(timezone=str(tzlocal.get_localzone()))


def schedule_show_subscription_monitor_job():
    job = scheduler.add_job(show_subscription_monitor_step,
                            trigger=IntervalTrigger(seconds=3600),
                            id="show_subscription_monitor",
                            max_instances=1,
                            )
    job.modify(next_run_time=datetime.now())
    logger.info("Started show subscription monitor")
    return True


def start():
    if schedule_show_subscription_monitor_job():
        scheduler.start()


if __name__ == '__main__':
    start()
