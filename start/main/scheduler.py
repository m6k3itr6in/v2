from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

logger = logging.getLogger(__name__)

def start():
    from main.utils import check_and_notify_understaffing
    
    scheduler = BackgroundScheduler()
    
    scheduler.add_job(
        check_and_notify_understaffing,
        trigger=CronTrigger(hour=10, minute=0),
        id="check_staffing_job",
        max_instances=1,
        replace_existing=True,
    )
    
    try:
        scheduler.start()
        print("--- Scheduler started successfully (Daily check at 10:00) ---")
    except Exception as e:
        print(f"--- Error starting scheduler: {e} ---")
