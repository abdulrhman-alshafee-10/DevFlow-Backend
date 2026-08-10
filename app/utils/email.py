"""
app/utils/email.py
──────────────────
Email sending utilities using fastapi-mail.
"""

from pathlib import Path
from typing import Any

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from app.config import get_settings

settings = get_settings()

conf = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_USER,
    MAIL_PASSWORD=settings.SMTP_PASSWORD,
    MAIL_FROM=settings.EMAILS_FROM_EMAIL,
    MAIL_PORT=settings.SMTP_PORT,
    MAIL_SERVER=settings.SMTP_HOST,
    MAIL_FROM_NAME=settings.EMAILS_FROM_NAME,
    MAIL_STARTTLS=settings.SMTP_TLS,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

async def send_email(
    email_to: str,
    subject: str,
    body: str,
    subtype: MessageType = MessageType.html
) -> None:
    """Sends an email using the configured SMTP server."""
    # For local development where SMTP is just an example, we might just print it
    # We will log it and optionally send if credentials are provided
    if settings.SMTP_HOST == "smtp.example.com":
        print(f"--- MOCK EMAIL ---")
        print(f"To: {email_to}")
        print(f"Subject: {subject}")
        print(f"Body: {body}")
        print(f"------------------")
        return

    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=body,
        subtype=subtype
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)
