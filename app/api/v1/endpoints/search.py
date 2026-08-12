import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_org_member, CurrentUser
from app.models.organization import Organization, OrganizationMember
from app.schemas.search import SearchResponse, SearchType
from app.services.search_service import SearchService

router = APIRouter()

OrgMemberDep = Annotated[tuple[Organization, OrganizationMember], Depends(require_org_member())]

@router.get(
    "",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Unified search across org",
)
async def search_all(
    org_ctx: OrgMemberDep,
    q: str = Query(..., min_length=1, description="Search query"),
    type: SearchType | None = Query(None, description="Filter by entity type"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db)
):
    org, membership = org_ctx
    service = SearchService(session)
    
    offset = (page - 1) * size
    type_str = type.value if type else None
    
    items, total = await service.search(
        org_id=org.id,
        query=q,
        entity_type=type_str,
        limit=size,
        offset=offset
    )
    
    return SearchResponse(
        results=items,
        total=total,
        page=page,
        size=size
    )

@router.get(
    "/tasks",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search tasks within org",
)
async def search_tasks(
    org_ctx: OrgMemberDep,
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db)
):
    org, membership = org_ctx
    service = SearchService(session)
    items, total = await service.search(org.id, q, "task", size, (page-1)*size)
    return SearchResponse(results=items, total=total, page=page, size=size)

@router.get(
    "/projects",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search projects within org",
)
async def search_projects(
    org_ctx: OrgMemberDep,
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db)
):
    org, membership = org_ctx
    service = SearchService(session)
    items, total = await service.search(org.id, q, "project", size, (page-1)*size)
    return SearchResponse(results=items, total=total, page=page, size=size)
