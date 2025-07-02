from typing import Dict, List
from fastapi import WebSocket
from uuid import UUID


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates
    """
    def __init__(self):
        # All active connections: {client_id: WebSocket}
        self.active_connections: Dict[UUID, WebSocket] = {}
        # User connections map: {user_id: [client_id1, client_id2, ...]}
        self.user_connections: Dict[str, List[UUID]] = {}

    async def connect(self, websocket: WebSocket, client_id: UUID, user_id: str = None):
        """
        Connect a client and associate it with a user if provided
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        
        # Associate with user if authenticated
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = []
            self.user_connections[user_id].append(client_id)

    def disconnect(self, client_id: UUID, user_id: str = None):
        """
        Disconnect a client and remove from user associations
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        
        # Remove from user connections if needed
        if user_id and user_id in self.user_connections:
            if client_id in self.user_connections[user_id]:
                self.user_connections[user_id].remove(client_id)
                # Clean up empty user entries
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]

    async def send_message(self, message: dict, client_id: UUID):
        """
        Send a message to a specific client
        """
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            await websocket.send_json(message)

    async def broadcast(self, message: dict):
        """
        Broadcast a message to all connected clients
        """
        for websocket in self.active_connections.values():
            await websocket.send_json(message)

    async def send_to_user(self, user_id: str, message: dict):
        """
        Send a message to all connections of a specific user
        """
        if user_id in self.user_connections:
            for client_id in self.user_connections[user_id]:
                await self.send_message(message, client_id)


# Global connection manager instance
manager = ConnectionManager()
