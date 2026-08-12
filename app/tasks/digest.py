from app.core.celery_app import celery_app
import asyncio
from datetime import datetime, timezone, timedelta

@celery_app.task(
    name="app.tasks.digest.generate_daily_digest_task",
    autoretry_for=(Exception,),
    max_retries=1
)
def generate_daily_digest_task():
    """
    Generates and sends a daily digest email to users.
    """
    async def _generate():
        # TODO: Implement digest logic (e.g. summarizing task activity)
        print("Generating daily digest...")
        
    asyncio.run(_generate())
