import uuid
from typing import Any
from sqlalchemy import select, func, literal_column, union_all, desc, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.models.project import Project
from app.models.comment import Comment

class SearchRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def search(
        self,
        org_id: uuid.UUID,
        query: str,
        entity_type: str | None = None,
        limit: int = 20,
        offset: int = 0
    ) -> tuple[list[dict[str, Any]], int]:
        
        is_sqlite = self.session.bind and self.session.bind.dialect.name == "sqlite"

        tsquery = func.websearch_to_tsquery('english', query)
        
        def make_match(col):
            if is_sqlite:
                return col.op("LIKE")(f"%{query}%")
            return col.op("@@")(tsquery)

        queries = []

        if entity_type in (None, "project"):
            q_proj = select(
                literal_column("'project'").label("type"),
                Project.id.label("id"),
                Project.name.label("title"),
                func.ts_headline('english', Project.description, tsquery, 'StartSel=<mark>, StopSel=</mark>').label("snippet"),
                func.ts_rank(Project.search_vector, tsquery).label("rank"),
                Project.created_at.label("created_at"),
                literal_column("NULL").cast(String).label("project_name")
            ).where(
                Project.organization_id == org_id,
                make_match(Project.search_vector)
            )
            queries.append(q_proj)

        if entity_type in (None, "task"):
            q_task = select(
                literal_column("'task'").label("type"),
                Task.id.label("id"),
                Task.title.label("title"),
                func.ts_headline('english', Task.description, tsquery, 'StartSel=<mark>, StopSel=</mark>').label("snippet"),
                func.ts_rank(Task.search_vector, tsquery).label("rank"),
                Task.created_at.label("created_at"),
                Project.name.label("project_name")
            ).select_from(Task).join(Project, Task.project_id == Project.id).where(
                Project.organization_id == org_id,
                make_match(Task.search_vector)
            )
            queries.append(q_task)
            
        if entity_type in (None, "comment"):
            q_comment = select(
                literal_column("'comment'").label("type"),
                Comment.id.label("id"),
                literal_column("''").label("title"),
                func.ts_headline('english', Comment.content, tsquery, 'StartSel=<mark>, StopSel=</mark>').label("snippet"),
                func.ts_rank(Comment.search_vector, tsquery).label("rank"),
                Comment.created_at.label("created_at"),
                Project.name.label("project_name")
            ).select_from(Comment).join(Task, Comment.task_id == Task.id).join(Project, Task.project_id == Project.id).where(
                Project.organization_id == org_id,
                make_match(Comment.search_vector)
            )
            queries.append(q_comment)

        if not queries:
            return [], 0

        # Union all and order by rank
        combined = union_all(*queries).subquery()
        
        # We need the total count
        count_query = select(func.count()).select_from(combined)
        total = await self.session.scalar(count_query)

        # Pagination
        final_query = select(combined).order_by(desc(combined.c.rank), desc(combined.c.created_at)).limit(limit).offset(offset)
        result = await self.session.execute(final_query)
        
        items = []
        for row in result.mappings():
            item = dict(row)
            # Ensure id and created_at are properly formatted for output (often handled by Pydantic, but let's make sure)
            items.append(item)
            
        return items, total or 0
