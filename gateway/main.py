from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx

AUTH_BASE = "http://localhost:8001"
CORE_BASE = "http://localhost:8000"

AUTH_PREFIXES = ("/api/v1/auth", "/api/v1/users")

app = FastAPI(title="SKALD Gateway", docs_url=None)

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

@app.get("/auth/docs", include_in_schema=False)
async def auth_docs_redirect():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"{AUTH_BASE}/docs")

@app.get("/core/docs", include_in_schema=False)
async def core_docs_redirect():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"{CORE_BASE}/docs")

async def _proxy(request: Request, target_base: str) -> StreamingResponse:
    url = httpx.URL(
        target_base + request.url.path,
        params=request.query_params,
    )
    headers = dict(request.headers)
    headers.pop("host", None)

    body = await request.body()

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=body,
        )

    return StreamingResponse(
        content=iter([resp.content]),
        status_code=resp.status_code,
        headers=dict(resp.headers),
    )

@app.api_route(
    "/api/v1/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
async def proxy(request: Request, path: str):
    full_path = "/api/v1/" + path
    target = AUTH_BASE if full_path.startswith(AUTH_PREFIXES) else CORE_BASE
    return await _proxy(request, target)

@app.api_route(
    "/static/{path:path}",
    methods=["GET"],
)
async def static_proxy(request: Request, path: str):
    return await _proxy(request, CORE_BASE)
