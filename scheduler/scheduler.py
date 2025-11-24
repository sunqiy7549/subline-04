"""APScheduler configuration and initialization."""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from scheduler.jobs import crawl_all_fast_sources, crawl_guangxi_source, cleanup_job

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None


def init_scheduler():
    """Initialize and start the background scheduler."""
    global scheduler
    
    if scheduler is not None:
        logger.warning("Scheduler already initialized")
        return scheduler
    
    logger.info("Initializing background scheduler...")
    
    # Create scheduler (use server's local timezone)
    scheduler = BackgroundScheduler(
        job_defaults={
            'coalesce': True,  # Combine multiple missed runs into one
            'max_instances': 1  # Only one instance of each job at a time
        }
    )
    
    # Schedule 1: Fast sources at 9:00 AM daily
    scheduler.add_job(
        func=crawl_all_fast_sources,
        trigger=CronTrigger(hour=9, minute=0),
        id='crawl_fast_sources',
        name='Crawl Fast Sources (Fujian, Hainan, Nanfang, Guangzhou)',
        replace_existing=True
    )
    logger.info("✓ Scheduled: Fast sources crawl at 09:00 AM daily")
    
    # Schedule 2: Guangxi at 9:30 AM daily (offset to avoid overlap)
    scheduler.add_job(
        func=crawl_guangxi_source,
        trigger=CronTrigger(hour=9, minute=30),
        id='crawl_guangxi',
        name='Crawl Guangxi Daily (Slow)',
        replace_existing=True
    )
    logger.info("✓ Scheduled: Guangxi crawl at 09:30 AM daily")
    
    # Schedule 3: Cleanup at 10:30 AM daily (after all crawls)
    scheduler.add_job(
        func=cleanup_job,
        trigger=CronTrigger(hour=10, minute=30),
        id='cleanup_old_articles',
        name='Cleanup Old Articles (7-day retention)',
        replace_existing=True
    )
    logger.info("✓ Scheduled: Cleanup at 10:30 AM daily")
    
    # Start the scheduler
    scheduler.start()
    logger.info("✓ Background scheduler started successfully")
    
    return scheduler


def shutdown_scheduler():
    """Shutdown the scheduler gracefully."""
    global scheduler
    
    if scheduler is not None:
        logger.info("Shutting down scheduler...")
        scheduler.shutdown(wait=True)
        scheduler = None
        logger.info("✓ Scheduler shut down")


def get_scheduler():
    """Get the scheduler instance (initialize if needed)."""
    global scheduler
    
    if scheduler is None:
        return init_scheduler()
    
    return scheduler


def trigger_job_now(job_id):
    """
    Manually trigger a scheduled job immediately.
    
    Args:
        job_id: Job ID (e.g., 'crawl_fast_sources', 'crawl_guangxi', 'cleanup_old_articles')
    
    Returns:
        True if triggered successfully, False otherwise
    """
    global scheduler
    
    if scheduler is None:
        logger.error("Scheduler not initialized")
        return False
    
    try:
        job = scheduler.get_job(job_id)
        if job is None:
            logger.error(f"Job '{job_id}' not found")
            return False
        
        logger.info(f"Manually triggering job: {job.name}")
        job.func()
        return True
        
    except Exception as e:
        logger.error(f"Failed to trigger job '{job_id}': {e}")
        return False


def get_next_run_times():
    """Get next run times for all scheduled jobs."""
    global scheduler
    
    if scheduler is None:
        return {}
    
    jobs = scheduler.get_jobs()
    next_runs = {}
    
    for job in jobs:
        next_runs[job.id] = {
            'name': job.name,
            'next_run': job.next_run_time.isoformat() if job.next_run_time else None
        }
    
    return next_runs
