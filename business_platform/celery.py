"""
Celery Configuration for Integrated Business Platform

This module configures Celery for background task processing,
including automated reminders, notifications, and scheduled tasks.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'business_platform.settings')

app = Celery('business_platform')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat Schedule for Periodic Tasks
app.conf.beat_schedule = {
    # Check and send reminders every 5 minutes
    'check-and-send-reminders': {
        'task': 'event_management.tasks.check_and_send_reminders',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    # Daily digest of upcoming events (8 AM daily)
    'daily-event-digest': {
        'task': 'event_management.tasks.send_daily_event_digest',
        'schedule': crontab(hour=8, minute=0),  # 8:00 AM every day
    },
    # Check for overdue events (every hour)
    'check-overdue-events': {
        'task': 'event_management.tasks.check_overdue_events',
        'schedule': crontab(minute=0),  # Every hour on the hour
    },
}

# Celery Configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Hong_Kong',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max per task
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery setup"""
    print(f'Request: {self.request!r}')
