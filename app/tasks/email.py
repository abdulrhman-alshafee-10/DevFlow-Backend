from app.core.celery_app import celery_app
from app.utils.email import send_email
import asyncio

@celery_app.task(
    name="app.tasks.email.send_email_task",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    max_retries=5
)
def send_email_task(email_to: str, subject: str, body: str, idempotency_key: str = None):
    """
    Sends an email synchronously in the Celery worker.
    Uses asyncio.run to call the async send_email function.
    """
    # For full idempotency, we can check/insert the idempotency_key in the DB.
    # We will need a synchronous DB session for this since Celery tasks are sync by default,
    # or we can wrap the entire logic in an async function and run it with asyncio.run().
    
    async def _send():
        if idempotency_key:
            from app.database import AsyncSessionLocal
            from sqlalchemy import select
            from app.models.email_log import EmailLog
            
            async with AsyncSessionLocal() as db:
                # Check if email was already sent
                result = await db.execute(select(EmailLog).where(EmailLog.id == idempotency_key))
                if result.scalar_one_or_none() is not None:
                    print(f"Email {idempotency_key} already sent. Skipping.")
                    return
                
                # Send email
                await send_email(email_to=email_to, subject=subject, body=body)
                
                # Log it
                new_log = EmailLog(id=idempotency_key, email_to=email_to, subject=subject)
                db.add(new_log)
                await db.commit()
        else:
            await send_email(email_to=email_to, subject=subject, body=body)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # During tests with task_always_eager=True, an event loop is already running.
        # We can create a task instead of using asyncio.run
        loop.create_task(_send())
    else:
        # Standard Celery worker execution
        asyncio.run(_send())
