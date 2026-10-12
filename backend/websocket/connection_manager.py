from fastapi import WebSocket
from typing import Dict, List
import json

class ConnectionManager:
    """Manages WebSocket connections for real-time analysis updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
    
    def disconnect(self, session_id: str):
        """Remove a WebSocket connection"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket"""
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        """Broadcast a message to all connected WebSockets"""
        for connection in self.active_connections.values():
            await connection.send_text(message)
    
    async def send_session_update(self, session_id: str, update: Dict):
        """Send an update to a specific session"""
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_text(json.dumps(update))
    
    async def send_progress(self, session_id: str, step: str, status: str):
        """Send progress update"""
        update = {
            "type": "progress",
            "step": step,
            "status": status
        }
        await self.send_session_update(session_id, update)
    
    async def send_result(self, session_id: str, result: Dict):
        """Send analysis result"""
        update = {
            "type": "result",
            "data": result
        }
        await self.send_session_update(session_id, update)
    
    async def send_error(self, session_id: str, error: str):
        """Send error message"""
        update = {
            "type": "error",
            "message": error
        }
        await self.send_session_update(session_id, update)
