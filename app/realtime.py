import json
from typing import List, Optional, Sequence

from fastapi import WebSocket


def _origin_allowed(origin: Optional[str], allowed_origins: Sequence[str]) -> bool:
    if not allowed_origins or '*' in allowed_origins:
        return True
    if not origin:
        return True
    return origin in list(allowed_origins)


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, allowed_origins: Optional[Sequence[str]] = None) -> bool:
        origin = websocket.headers.get('origin')
        if allowed_origins is not None and not _origin_allowed(origin, allowed_origins):
            await websocket.close(code=1008)
            return False
        await websocket.accept()
        self.active_connections.append(websocket)
        return True

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                dead_connections.append(connection)
        for connection in dead_connections:
            self.disconnect(connection)
