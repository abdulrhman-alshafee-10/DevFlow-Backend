import uuid
from datetime import date

from sqlalchemy import String, Text, Date, Integer, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Task(BaseModel):
    __tablename__ = "tasks"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="todo", server_default="todo"
    )
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False, default="medium", server_default="medium"
    )
    creator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    parent_task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True
    )
    position: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="tasks", lazy="noload")
    creator: Mapped["User"] = relationship("User", foreign_keys=[creator_id], lazy="noload")
    assignee: Mapped["User"] = relationship("User", foreign_keys=[assignee_id], lazy="noload")
    parent_task: Mapped["Task"] = relationship(
        "Task", remote_side="Task.id", back_populates="subtasks", lazy="noload"
    )
    subtasks: Mapped[list["Task"]] = relationship(
        "Task", back_populates="parent_task", cascade="all, delete-orphan", lazy="noload"
    )
    comments: Mapped[list["Comment"]] = relationship(
        "Comment", back_populates="task", cascade="all, delete-orphan", lazy="noload"
    )

    __table_args__ = (
        Index("ix_tasks_project_id_status", "project_id", "status"),
        Index(
            "ix_tasks_fts",
            func.to_tsvector("english", title + " " + func.coalesce(description, "")),
            postgresql_using="gin",
        ),
    )

    def __repr__(self) -> str:
        return f"<Task id={self.id} title={self.title!r}>"
