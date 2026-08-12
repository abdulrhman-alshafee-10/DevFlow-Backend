import uuid

from sqlalchemy import Text, ForeignKey, Index, Computed
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Any

from app.models.base import BaseModel


class Comment(BaseModel):
    __tablename__ = "comments"
    __table_args__ = (
        Index("ix_comments_search", "search_vector", postgresql_using="gin"),
    )

    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    search_vector: Mapped[Any] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('english', content)"),
    )

    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="comments", lazy="noload")
    author: Mapped["User"] = relationship("User", lazy="noload")

    def __repr__(self) -> str:
        return f"<Comment id={self.id} task_id={self.task_id}>"
