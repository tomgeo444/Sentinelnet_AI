"""
SentinelNet AI - Real-Time WebSocket Connection Manager
Broadcasts live detection events, telemetry, and security alerts to connected dashboards.
"""

import json
import logging
import asyncio
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("sentinelnet.websocket")


class ConnectionManager:
    """Manages active WebSocket connections and broadcasts JSON messages."""
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        """Accepts and registers a new WebSocket client."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Active clients: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        """Unregisters a disconnected WebSocket client."""
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Remaining clients: {len(self.active_connections)}")

    async def broadcast_json(self, message: dict):
        """Broadcasts a JSON dictionary to all connected clients concurrently."""
        if not self.active_connections:
            return

        async with self._lock:
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.debug(f"Failed to send to client ({e}). Marking for cleanup.")
                    disconnected.append(connection)

            for conn in disconnected:
                if conn in self.active_connections:
                    self.active_connections.remove(conn)

    def broadcast_sync(self, message: dict, loop: asyncio.AbstractEventLoop = None):
        """Helper to safely broadcast from synchronous background worker threads."""
        if loop and loop.is_running():
            asyncio.run_coroutine_threadsafe(self.broadcast_json(message), loop)


ws_manager = ConnectionManager()
