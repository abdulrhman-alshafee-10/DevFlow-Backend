import uuid
from typing import Any

from sqlalchemy import String, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class AuditLog(BaseModel):
    __tablename__ = "audit_log"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    changes: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", lazy="noload")
    actor: Mapped["User"] = relationship("User", lazy="noload")

    __table_args__ = (
        Index("ix_audit_log_entity", "entity_type", "entity_id"),
        Index("ix_audit_log_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} entity={self.entity_type}:{self.entity_id} action={self.action}>"
