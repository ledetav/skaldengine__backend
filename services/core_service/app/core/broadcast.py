"""Менеджер WebSocket-соединений для рассылки широковещательных сообщений."""

from typing import List
from fastapi import WebSocket


class ConnectionManager:
    """Управляет активными WebSocket-соединениями клиентов."""

    def __init__(self):
        """Инициализация списка активных соединений."""
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Принимает новое WebSocket-соединение и сохраняет его в списке активных."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """Удаляет закрытое WebSocket-соединение из списка активных."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Отправляет JSON-сообщение всем активным подключенным клиентам."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # Соединение могло быть уже разорвано клиентом
                continue


manager = ConnectionManager()

