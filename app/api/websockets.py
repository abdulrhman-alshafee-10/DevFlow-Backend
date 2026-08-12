"""
app/api/websockets.py
─────────────────────
WebSocket endpoints for real-time features.
"""
import json
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, WebSocketException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_ws, get_db
from app.core.realtime import manager
from app.models.user import User
from app.repositories.project import ProjectMemberRepository

router = APIRouter()

@router.websocket("/projects/{project_id}/tasks")
async def project_tasks_websocket(
    websocket: WebSocket,
    project_id: UUID,
    current_user: User = Depends(get_current_user_ws),
    db: AsyncSession = Depends(get_db),
):
    """
    WebSocket endpoint for project task updates.
    """
    if not current_user.is_superuser:
        member_repo = ProjectMemberRepository(db)
        membership = await member_repo.get_membership(project_id, current_user.id)
        if not membership:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION, 
                reason="Not a member of this project"
            )

    await manager.connect(websocket)
    channel = f"project_{project_id}"
    await manager.subscribe(websocket, channel)
    try:
        while True:
            # We don't expect messages from the client right now, just keep connection open
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)

@router.websocket("/notifications")
async def notifications_websocket(
    websocket: WebSocket,
    current_user: User = Depends(get_current_user_ws),
):
    """
    WebSocket endpoint for real-time user notifications.
    """
    await manager.connect(websocket)
    channel = f"user_{current_user.id}"
    await manager.subscribe(websocket, channel)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)

@router.websocket("/chat/{room_id}")
async def chat_websocket(
    websocket: WebSocket,
    room_id: UUID,
    current_user: User = Depends(get_current_user_ws),
):
    """
    WebSocket endpoint for a chat room.
    """
    await manager.connect(websocket)
    channel = f"chat_{room_id}"
    await manager.subscribe(websocket, channel)
    try:
        while True:
            data = await websocket.receive_text()
            
            # Publish incoming chat message to Redis
            message = {
                "type": "chat_message",
                "payload": {
                    "text": data,
                    "user": {
                        "id": str(current_user.id),
                        "name": f"{current_user.first_name} {current_user.last_name}".strip()
                    }
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            await manager.publish(channel, message)
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
