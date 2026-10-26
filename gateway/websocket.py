"""Модуль двунаправленного WebSocket-проксирования для API Gateway.

Обеспечивает установку и поддержание соединений с Core Service
с передачей токенов авторизации и параметров запроса.
"""
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
import websockets as ws_lib

from gateway.config import CORE_BASE, logger


def _ws_url(http_base: str, path: str) -> str:
    """Преобразует http(s):// в ws(s):// для WebSocket подключений."""
    base = http_base.replace("https://", "wss://").replace("http://", "ws://")
    return base.rstrip("/") + path


async def websocket_proxy_handler(websocket: WebSocket, path: str) -> None:
    """Проксирует WebSocket соединения к core-сервису."""
    target_url = _ws_url(CORE_BASE, f"/api/v1/ws/{path}")

    # Перенаправляем параметры строки запроса (например, ?token=...)
    if websocket.query_params:
        qs = "&".join(f"{k}={v}" for k, v in websocket.query_params.items())
        target_url = f"{target_url}?{qs}"

    # Перенаправляем заголовок Authorization при наличии
    extra_headers = {}
    if auth := websocket.headers.get("authorization"):
        extra_headers["Authorization"] = auth

    logger.info(f"WS proxy: {target_url}")

    try:
        async with ws_lib.connect(target_url, additional_headers=extra_headers) as backend_ws:
            await websocket.accept()

            async def client_to_backend():
                try:
                    while True:
                        data = await websocket.receive_text()
                        await backend_ws.send(data)
                except (WebSocketDisconnect, Exception):
                    pass

            async def backend_to_client():
                try:
                    async for message in backend_ws:
                        if isinstance(message, str):
                            await websocket.send_text(message)
                        else:
                            await websocket.send_bytes(message)
                except Exception:
                    pass

            await asyncio.gather(client_to_backend(), backend_to_client())

    except ws_lib.exceptions.WebSocketException as e:
        logger.error(f"WS proxy error connecting to {target_url}: {e}")
        await websocket.close(code=1011, reason="Backend WebSocket unavailable")
    except Exception as e:
        logger.error(f"WS proxy unexpected error: {e}")
        try:
            await websocket.close(code=1011)
        except Exception:
            pass
