import uuid
from fastapi import APIRouter, Depends, status

from app.api.deps import CurrentUser, get_current_user
from app.schemas.comment import CommentResponse, CommentUpdate
from app.api.v1.tasks import get_comment_service, CommentService


router = APIRouter(
    prefix="/comments",
    tags=["comments"],
    dependencies=[Depends(get_current_user)],
)


@router.patch(
    "/{comment_id}",
    response_model=CommentResponse,
    summary="Edit comment",
)
async def update_comment(
    comment_id: uuid.UUID,
    data: CommentUpdate,
    current_user: CurrentUser,
    service: CommentService = Depends(get_comment_service),
) -> CommentResponse:
    comment = await service.update_comment(comment_id, data, current_user)
    return CommentResponse.model_validate(comment)


@router.delete(
    "/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete comment",
)
async def delete_comment(
    comment_id: uuid.UUID,
    current_user: CurrentUser,
    service: CommentService = Depends(get_comment_service),
) -> None:
    await service.delete_comment(comment_id, current_user)
