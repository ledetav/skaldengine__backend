import traceback
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import JSONResponse
import httpx

from gateway.config import AUTH_BASE, CORE_BASE, AUTH_PREFIXES, logger
from gateway.cors import is_origin_allowed, cors_middleware
from gateway.proxy import _fetch, _proxy, _proxy_docs
from gateway.websocket import websocket_proxy_handler
from gateway.routers import system_router, docs_router

app = FastAPI(title="SKALD Gateway", docs_url=None)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"GATEWAY ERROR on {request.method} {request.url.path}: {str(exc)}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": f"Gateway Error: {exc.__class__.__name__} - {str(exc)}"},
    )


# Регистрируем CORS middleware
app.middleware("http")(cors_middleware)

# Подключаем роутеры системных и документационных эндпоинтов
app.include_router(system_router)
app.include_router(docs_router)


# ── Проксирование общих API запросов ──────────────────────────────────────────

@app.api_route(
    "/api/v1/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def api_proxy(request: Request, path: str):
    full_path = "/api/v1/" + path
    target = AUTH_BASE if full_path.startswith(AUTH_PREFIXES) else CORE_BASE
    return await _proxy(full_path, target, request)


@app.api_route("/static/{path:path}", methods=["GET"])
async def static_proxy(request: Request, path: str):
    return await _proxy("/static/" + path, CORE_BASE, request)


# ── Проксирование WebSocket соединений ────────────────────────────────────────

@app.websocket("/api/v1/ws/{path:path}")
async def websocket_proxy(websocket: WebSocket, path: str):
    await websocket_proxy_handler(websocket, path)
