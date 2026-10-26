"""WebSocket-эндпоинт для доставки обновлений в реальном времени."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.broadcast import manager

router = APIRouter()


@router.websocket("/updates")
async def websocket_endpoint(websocket: WebSocket):
    """Принимает постоянное WebSocket-соединение для отправки обновлений клиенту."""
    await manager.connect(websocket)
    try:
        while True:
            # Поддерживаем соединение активным
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

