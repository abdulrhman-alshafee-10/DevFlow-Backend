import uuid

from sqlalchemy import Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Comment(BaseModel):
    __tablename__ = "comments"

    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="comments", lazy="noload")
    author: Mapped["User"] = relationship("User", lazy="noload")

    def __repr__(self) -> str:
        return f"<Comment id={self.id} task_id={self.task_id}>"
