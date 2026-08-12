import uuid
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.search_repository import SearchRepository

class SearchService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.search_repo = SearchRepository(session)

    async def search(
        self,
        org_id: uuid.UUID,
        query: str,
        entity_type: str | None = None,
        limit: int = 20,
        offset: int = 0
    ) -> tuple[list[dict[str, Any]], int]:
        """
        Perform a unified search across projects, tasks, and comments within an organization.
        Assumes the caller has already verified the user's membership in the organization.
        """
        return await self.search_repo.search(
            org_id=org_id,
            query=query,
            entity_type=entity_type,
            limit=limit,
            offset=offset
        )
