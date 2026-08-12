"""
app/core/realtime.py
────────────────────
Real-time connection manager using WebSockets and Redis Pub/Sub.
"""

import asyncio
import json
import logging
from typing import Dict, Set

from fastapi import WebSocket

from app.utils.redis import RedisManager

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        # Maps channel name to a set of active WebSockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Keep track of which channels a WebSocket is subscribed to
        self.websocket_channels: Dict[WebSocket, Set[str]] = {}
        self.pubsub = None
        self.listener_task = None

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.websocket_channels[websocket] = set()

    async def subscribe(self, websocket: WebSocket, channel: str) -> None:
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
            # If this is the first local connection for this channel, subscribe to Redis
            if self.pubsub is not None:
                await self.pubsub.subscribe(channel)
        
        self.active_connections[channel].add(websocket)
        self.websocket_channels[websocket].add(channel)

    async def unsubscribe(self, websocket: WebSocket, channel: str) -> None:
        if channel in self.active_connections and websocket in self.active_connections[channel]:
            self.active_connections[channel].remove(websocket)
            if not self.active_connections[channel]:
                del self.active_connections[channel]
                # If no more local subscribers, unsubscribe from Redis
                if self.pubsub is not None:
                    await self.pubsub.unsubscribe(channel)
        
        if websocket in self.websocket_channels and channel in self.websocket_channels[websocket]:
            self.websocket_channels[websocket].remove(channel)

    async def disconnect(self, websocket: WebSocket) -> None:
        channels = self.websocket_channels.pop(websocket, set())
        for channel in list(channels):
            await self.unsubscribe(websocket, channel)

    async def broadcast_local(self, channel: str, message: str) -> None:
        """Send message to all local websockets subscribed to the channel."""
        if channel in self.active_connections:
            dead_sockets = set()
            for connection in self.active_connections[channel]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.warning(f"Error sending to websocket: {e}")
                    dead_sockets.add(connection)
            
            for dead in dead_sockets:
                await self.disconnect(dead)

    async def publish(self, channel: str, message: dict) -> None:
        """Publish a message to Redis."""
        redis = RedisManager.get_client()
        await redis.publish(channel, json.dumps(message))

    async def _listen_to_redis(self) -> None:
        """Background task to listen to Redis Pub/Sub."""
        redis = RedisManager.get_client()
        self.pubsub = redis.pubsub()
        # Subscribe to a dummy channel so the listener loop doesn't fail if no real channels exist yet.
        await self.pubsub.subscribe("devflow_control") 
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    channel = message["channel"]
                    data = message["data"]
                    await self.broadcast_local(channel, data)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Redis pub/sub listener error: {e}")
        finally:
            if self.pubsub:
                await self.pubsub.close()

    async def startup(self) -> None:
        self.listener_task = asyncio.create_task(self._listen_to_redis())

    async def shutdown(self) -> None:
        if self.listener_task:
            self.listener_task.cancel()
            try:
                await self.listener_task
            except asyncio.CancelledError:
                pass


# Global singleton instance
manager = ConnectionManager()
