from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.broadcast import manager

router = APIRouter()

@router.websocket("/updates")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, consume messages if any
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
