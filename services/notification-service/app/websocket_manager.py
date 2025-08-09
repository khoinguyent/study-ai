import json
import asyncio
from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
from .schemas import WebSocketMessage

class WebSocketManager:
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Store connection to user mapping
        self.connection_to_user: Dict[WebSocket, str] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Connect a new WebSocket connection for a user"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        self.connection_to_user[websocket] = user_id
        
        print(f"User {user_id} connected. Total connections: {len(self.active_connections[user_id])}")
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket connection"""
        user_id = self.connection_to_user.get(websocket)
        if user_id:
            self.active_connections[user_id].discard(websocket)
            del self.connection_to_user[websocket]
            
            # Clean up empty user connections
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
            
            print(f"User {user_id} disconnected. Remaining connections: {len(self.active_connections.get(user_id, set()))}")
    
    async def send_notification(self, user_id: str, message: dict):
        """Send a notification message to a specific user"""
        if user_id in self.active_connections:
            disconnected_websockets = set()
            
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    print(f"Error sending notification to user {user_id}: {e}")
                    disconnected_websockets.add(websocket)
            
            # Clean up disconnected websockets
            for websocket in disconnected_websockets:
                self.disconnect(websocket)
    
    async def send_personal_message(self, message: WebSocketMessage, user_id: str):
        """Send a message to a specific user"""
        if user_id in self.active_connections:
            disconnected_websockets = set()
            
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_text(message.json())
                except Exception as e:
                    print(f"Error sending message to user {user_id}: {e}")
                    disconnected_websockets.add(websocket)
            
            # Clean up disconnected websockets
            for websocket in disconnected_websockets:
                self.disconnect(websocket)
    
    async def broadcast_task_status(self, user_id: str, task_id: str, status: str, progress: int, message: str = None):
        """Broadcast task status update to a specific user"""
        websocket_message = WebSocketMessage(
            type="task_status",
            data={
                "task_id": task_id,
                "status": status,
                "progress": progress,
                "message": message,
                "timestamp": asyncio.get_event_loop().time()
            }
        )
        await self.send_personal_message(websocket_message, user_id)
    
    async def broadcast_notification(self, user_id: str, title: str, message: str, notification_type: str = "task_status"):
        """Broadcast notification to a specific user"""
        websocket_message = WebSocketMessage(
            type="notification",
            data={
                "title": title,
                "message": message,
                "notification_type": notification_type,
                "timestamp": asyncio.get_event_loop().time()
            }
        )
        await self.send_personal_message(websocket_message, user_id)
    
    def get_active_users(self) -> Set[str]:
        """Get all active user IDs"""
        return set(self.active_connections.keys())
    
    def get_user_connection_count(self, user_id: str) -> int:
        """Get number of active connections for a user"""
        return len(self.active_connections.get(user_id, set()))

# Global WebSocket manager instance
websocket_manager = WebSocketManager() 