import uuid
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(AuditLog, session)

    async def log_action(
        self,
        organization_id: uuid.UUID,
        entity_type: str,
        entity_id: uuid.UUID,
        action: str,
        actor_id: uuid.UUID,
        changes: dict[str, Any] | None = None,
    ) -> AuditLog:
        log = AuditLog(
            organization_id=organization_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor_id=actor_id,
            changes=changes,
        )
        self.session.add(log)
        await self.session.flush()
        await self.session.refresh(log)
        return log

    async def get_history(
        self,
        entity_type: str,
        entity_id: uuid.UUID,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[AuditLog], int]:
        stmt = select(AuditLog).where(
            AuditLog.entity_type == entity_type,
            AuditLog.entity_id == entity_id,
        )
        
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = stmt.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        
        return list(result.scalars().all()), total
