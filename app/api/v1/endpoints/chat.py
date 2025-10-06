from typing import List

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app import schemas
from app.api import deps
from app.db.models.user import User, Role
from app.db.models.message import Message, RecipientRole
from datetime import datetime, timezone


router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: str, user_id: int):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)

manager = ConnectionManager()

@router.post("/send")
async def send_message(
    *,
    db: AsyncSession = Depends(deps.get_db),
    message_in: schemas.MessageCreate,
    current_user: User = Depends(deps.get_current_active_user)
):
    print(">>> received:", message_in.recipient_role, type(message_in.recipient_role))
    db_message = Message(
    sender_id=current_user.id,
    recipient_role=message_in.recipient_role.value.upper(),
    content=message_in.content,
    timestamp=datetime.now(timezone.utc),
)
    db.add(db_message)
    await db.commit()
    await db.refresh(db_message)

    # Real-time broadcast
    if message_in.recipient_role == RecipientRole.ALL:
        await manager.broadcast(f"{current_user.username}: {message_in.content}")
    else:
        users = await db.execute(
            select(User).filter(User.role == Role[message_in.recipient_role.value.upper()])
        )
        for user in users.scalars().all():
            await manager.send_personal_message(
                f"{current_user.username}: {message_in.content}", user.id
            )

    return {"msg": "Message sent"}

@router.get("/messages/{role}", response_model=List[schemas.MessageRead])
async def get_messages(
    role: RecipientRole,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> List[Message]:
    result = await db.execute(
        select(Message)
        .filter((Message.recipient_role == role) | (Message.recipient_role == RecipientRole.ALL))
        .order_by(Message.timestamp.desc())
    )
    return result.scalars().all()

@router.get("/ws-docs/{user_id}")
async def websocket_docs(user_id: int):
    """
    This endpoint provides documentation for the websocket endpoint.

    To connect to the websocket, use the following URL:

    `ws://<host>/api/v1/chat/ws/{user_id}?token=<your-token>`
    """
    return {
        "websocket_url": f"ws://<host>/api/v1/chat/ws/{user_id}?token=<your-token>",
        "description": "WebSocket endpoint for real-time chat updates."
    }

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: int,
    token: str = Query(...),
    db: AsyncSession = Depends(deps.get_db),
):
    user = await deps.get_current_user_from_token(db, token)
    if not user or user.id != user_id:
        await websocket.close(code=1008)
        return

    await manager.connect(user.id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message_in = schemas.MessageCreate(recipient_role=RecipientRole.ALL, content=data)
            db_message = Message(**message_in.dict(), sender_id=user.id)
            db.add(db_message)
            await db.commit()
            await db.refresh(db_message)
            await manager.broadcast(f"{user.username}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(user.id)
