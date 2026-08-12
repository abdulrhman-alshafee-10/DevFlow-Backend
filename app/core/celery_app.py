import os
from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "devflow_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.email", "app.tasks.cleanup", "app.tasks.digest"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_always_eager=settings.ENVIRONMENT == "development", # Fallback for local dev without Redis
    task_eager_propagates=True,
)

# Optional: define beat schedule
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    "clean-expired-tokens-daily": {
        "task": "app.tasks.cleanup.clean_expired_tokens_task",
        "schedule": crontab(hour=2, minute=0),
    },
    "clean-old-notifications-weekly": {
        "task": "app.tasks.cleanup.clean_old_notifications_task",
        "schedule": crontab(day_of_week="sunday", hour=3, minute=0),
    },
    "generate-daily-digest": {
        "task": "app.tasks.digest.generate_daily_digest_task",
        "schedule": crontab(hour=8, minute=0),
    },
}
