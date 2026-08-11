import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment
from app.repositories.base import BaseRepository


class CommentRepository(BaseRepository[Comment]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Comment, session)

    async def list_comments(
        self,
        task_id: uuid.UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Comment], int]:
        stmt = select(Comment).where(Comment.task_id == task_id)
        
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = stmt.order_by(Comment.created_at.asc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        
        return list(result.scalars().all()), total
