from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from datetime import datetime

from app.models.base import Base

class EmailLog(Base):
    __tablename__ = "email_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True) # E.g., unique idempotency key like email:subject:user_id
    email_to: Mapped[str] = mapped_column(String, nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
