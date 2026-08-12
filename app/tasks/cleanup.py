from app.core.celery_app import celery_app
import asyncio

@celery_app.task(
    name="app.tasks.cleanup.clean_expired_tokens_task",
    autoretry_for=(Exception,),
    max_retries=1
)
def clean_expired_tokens_task():
    """
    Cleans up expired refresh tokens and password reset tokens from the database.
    """
    async def _clean():
        # TODO: Implement actual deletion logic using repositories
        print("Cleaning expired tokens...")
    
    asyncio.run(_clean())

@celery_app.task(
    name="app.tasks.cleanup.clean_old_notifications_task",
    autoretry_for=(Exception,),
    max_retries=1
)
def clean_old_notifications_task():
    """
    Cleans up read notifications older than a certain threshold.
    """
    async def _clean():
        # TODO: Implement actual deletion logic
        print("Cleaning old notifications...")
        
    asyncio.run(_clean())
