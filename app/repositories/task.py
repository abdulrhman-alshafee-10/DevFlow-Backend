import uuid

from sqlalchemy import select, func, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Task, session)

    async def list_tasks(
        self,
        project_id: uuid.UUID,
        status: str | None = None,
        priority: str | None = None,
        assignee_id: uuid.UUID | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Task], int]:
        stmt = select(Task).where(Task.project_id == project_id)

        if status:
            stmt = stmt.where(Task.status == status)
        if priority:
            stmt = stmt.where(Task.priority == priority)
        if assignee_id:
            stmt = stmt.where(Task.assignee_id == assignee_id)
        if search:
            # PostgreSQL full text search
            tsvector = func.to_tsvector("english", Task.title + " " + func.coalesce(Task.description, ""))
            tsquery = func.websearch_to_tsquery("english", search)
            stmt = stmt.where(tsvector.op("@@")(tsquery))

        # Sort mapping
        sort_column = getattr(Task, sort_by, Task.created_at)
        if sort_order == "desc":
            stmt = stmt.order_by(desc(sort_column))
        else:
            stmt = stmt.order_by(asc(sort_column))

        # Count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one()

        # Paginate
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        
        return list(result.scalars().all()), total

    async def list_my_tasks(
        self,
        user_id: uuid.UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Task], int]:
        stmt = select(Task).where(Task.assignee_id == user_id)
        
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = stmt.order_by(Task.due_date.asc().nulls_last(), Task.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        
        return list(result.scalars().all()), total
