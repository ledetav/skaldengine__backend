import logging
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, HTMLResponse, Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("gateway")

AUTH_BASE = "http://127.0.0.1:8001"
CORE_BASE = "http://127.0.0.1:8000"

AUTH_PREFIXES = ("/api/v1/auth", "/api/v1/users")

app = FastAPI(title="SKALD Gateway", docs_url=None)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Global Error: {exc.__class__.__name__} - {str(exc)}"},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "gateway"}


@app.get("/debug/health")
async def debug_health():
    """Check connectivity to all backend services."""
    import asyncio
    results = {}
    for name, base in [("auth", AUTH_BASE), ("core", CORE_BASE)]:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"{base}/health")
                results[name] = {"status": "ok", "http_status": r.status_code, "url": base}
        except httpx.ConnectError as e:
            results[name] = {"status": "unreachable", "error": "Connection refused — service is down", "url": base}
        except Exception as e:
            results[name] = {"status": "error", "error": str(e), "url": base}
    overall = "ok" if all(v["status"] == "ok" for v in results.values()) else "degraded"
    return {"gateway": "ok", "services": results, "overall": overall}


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "skald-engine",
        "docs": {
            "auth": "/auth/docs",
            "core": "/core/docs",
        }
    }


async def _fetch(path: str, target_base: str, request: Request) -> httpx.Response:
    url = httpx.URL(target_base + path, params=request.query_params)
    headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}
    body = await request.body()
    
    logger.info(f"Proxying {request.method} request to: {url}")
    
    async with httpx.AsyncClient(timeout=120) as client:
        return await client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=body,
            follow_redirects=True,
        )


async def _proxy(path: str, target_base: str, request: Request) -> Response:
    try:
        resp = await _fetch(path, target_base, request)
        excluded = {"content-encoding", "transfer-encoding", "content-length"}
        headers = {k: v for k, v in resp.headers.items() if k.lower() not in excluded}
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=headers,
            media_type=resp.headers.get("content-type"),
        )
    except httpx.RequestError as e:
        error_msg = f"Network error proxying to {target_base}{path}: {e}"
        logger.error(error_msg, exc_info=True)
        return JSONResponse(status_code=502, content={"detail": f"Bad Gateway: {e.__class__.__name__} - {str(e)}"})
    except Exception as e:
        error_msg = f"Unexpected error proxying to {target_base}{path}: {e}"
        logger.error(error_msg, exc_info=True)
        return JSONResponse(status_code=500, content={"detail": f"Internal Gateway Server Error: {e.__class__.__name__} - {str(e)}"})


async def _proxy_docs(docs_path: str, openapi_path: str,
                      target_base: str, prefix: str, request: Request) -> Response:
    try:
        resp = await _fetch(docs_path, target_base, request)
        html = resp.text
        # Rewrite the openapi.json URL so the browser fetches it through the gateway
        html = html.replace(
            f"url: '{openapi_path}'",
            f"url: '/{prefix}{openapi_path}'"
        )
        return HTMLResponse(content=html, status_code=resp.status_code)
    except Exception as e:
        error_msg = f"Error proxying docs for {target_base}{docs_path}: {e}"
        logger.error(error_msg, exc_info=True)
        return JSONResponse(status_code=502, content={"detail": f"Docs Gateway Error: {e.__class__.__name__} - {str(e)}"})


# ── Auth docs ────────────────────────────────────────────────────────────────

@app.get("/auth/docs", include_in_schema=False)
async def auth_docs(request: Request):
    return await _proxy_docs(
        docs_path="/docs",
        openapi_path="/api/v1/openapi.json",
        target_base=AUTH_BASE,
        prefix="auth",
        request=request,
    )


@app.get("/auth/api/v1/openapi.json", include_in_schema=False)
async def auth_openapi(request: Request):
    return await _proxy("/api/v1/openapi.json", AUTH_BASE, request)


# ── Core docs ────────────────────────────────────────────────────────────────

@app.get("/core/docs", include_in_schema=False)
async def core_docs(request: Request):
    return await _proxy_docs(
        docs_path="/docs",
        openapi_path="/api/v1/openapi.json",
        target_base=CORE_BASE,
        prefix="core",
        request=request,
    )


@app.get("/core/api/v1/openapi.json", include_in_schema=False)
async def core_openapi(request: Request):
    return await _proxy("/api/v1/openapi.json", CORE_BASE, request)


# ── API proxy ────────────────────────────────────────────────────────────────

@app.api_route(
    "/api/v1/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
async def api_proxy(request: Request, path: str):
    full_path = "/api/v1/" + path
    target = AUTH_BASE if full_path.startswith(AUTH_PREFIXES) else CORE_BASE
    return await _proxy(full_path, target, request)


@app.api_route("/static/{path:path}", methods=["GET"])
async def static_proxy(request: Request, path: str):
    return await _proxy("/static/" + path, CORE_BASE, request)
