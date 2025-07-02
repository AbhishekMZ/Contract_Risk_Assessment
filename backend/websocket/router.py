from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from uuid import UUID, uuid4
from typing import Optional

from .connection_manager import manager
from .events import EventType, create_event

# For authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Create router
router = APIRouter(tags=["websocket"])


async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> Optional[str]:
    """
    Verify JWT token and extract user_id
    This is a simplified version - in production, implement proper JWT verification
    """
    try:
        from jose import jwt
        from datetime import datetime

        # In production, use proper secret key from environment variables
        SECRET_KEY = "your-secret-key-here"
        ALGORITHM = "HS256"

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        # Check if token is expired
        if payload.get("exp") and datetime.utcnow().timestamp() > payload.get("exp"):
            return None
            
        return user_id
    except Exception:
        return None


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for anonymous connections
    """
    client_id = uuid4()
    await manager.connect(websocket, client_id)
    
    try:
        # Send connection established event
        await manager.send_message(
            create_event(
                EventType.CONNECTION_ESTABLISHED,
                {"client_id": str(client_id), "authenticated": False}
            ),
            client_id
        )
        
        # Handle incoming messages
        while True:
            data = await websocket.receive_json()
            # Process incoming messages if needed
            # This is a simplified version, add message handling as required
    except WebSocketDisconnect:
        manager.disconnect(client_id)


@router.websocket("/ws/authenticated")
async def websocket_authenticated(
    websocket: WebSocket,
    token: Optional[str] = None
):
    """
    WebSocket endpoint for authenticated connections
    Authentication token is passed as a query parameter
    """
    client_id = uuid4()
    user_id = None
    
    # Verify token if provided
    if token:
        user_id = await get_current_user_id(token)
    
    # Connect with or without authentication
    await manager.connect(websocket, client_id, user_id)
    
    try:
        # Send connection established event with auth status
        await manager.send_message(
            create_event(
                EventType.CONNECTION_ESTABLISHED,
                {
                    "client_id": str(client_id),
                    "authenticated": user_id is not None,
                    "user_id": user_id if user_id else None
                }
            ),
            client_id
        )
        
        # Handle incoming messages
        while True:
            data = await websocket.receive_json()
            # Process authenticated messages
            # This is a simplified version, add message handling as required
    except WebSocketDisconnect:
        manager.disconnect(client_id, user_id)


# This function should be used in the main FastAPI app to include these routes
def include_websocket_routes(app):
    """
    Include WebSocket routes in the main FastAPI application
    """
    app.include_router(router)
