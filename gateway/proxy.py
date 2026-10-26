from fastapi import Request
from fastapi.responses import HTMLResponse, Response, JSONResponse, StreamingResponse
import httpx

from gateway.config import logger


async def _fetch(path: str, target_base: str, request: Request) -> httpx.Response:
    """Выполняет внутренний HTTP-запрос к целевому микросервису."""
    url = httpx.URL(target_base + path, params=request.query_params)
    excluded_headers = {"host", "origin", "referer"}
    headers = {k: v for k, v in request.headers.items() if k.lower() not in excluded_headers}
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
    """
    Проксирует HTTP-запрос к микросервису с поддержкой потоковых ответов (SSE)
    и защитой от буферизации обратными прокси.
    """
    url = httpx.URL(target_base + path, params=request.query_params)
    excluded_headers = {"host", "origin", "referer", "content-length"}
    headers = {k: v for k, v in request.headers.items() if k.lower() not in excluded_headers}
    body = await request.body()

    logger.info(f"Proxying {request.method} request to: {url}")

    # 120s connect/write timeout, infinite read timeout for SSE streams
    client = httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0, read=None))
    try:
        req = client.build_request(
            method=request.method,
            url=url,
            headers=headers,
            content=body,
        )
        upstream_resp = await client.send(req, stream=True, follow_redirects=True)

        excluded_resp = {"content-encoding", "transfer-encoding", "content-length"}
        resp_headers = {k: v for k, v in upstream_resp.headers.items() if k.lower() not in excluded_resp}
        content_type = upstream_resp.headers.get("content-type", "")

        is_stream = "text/event-stream" in content_type or path.endswith("/stream")

        if is_stream:
            # Предотвращаем буферизацию в Nginx / Caddy
            resp_headers["X-Accel-Buffering"] = "no"
            resp_headers["Cache-Control"] = "no-cache, no-transform"

            async def body_stream():
                try:
                    async for chunk in upstream_resp.aiter_raw():
                        yield chunk
                finally:
                    await upstream_resp.aclose()
                    await client.aclose()

            return StreamingResponse(
                body_stream(),
                status_code=upstream_resp.status_code,
                headers=resp_headers,
                media_type=content_type or "text/event-stream",
            )
        else:
            try:
                content = await upstream_resp.aread()
            finally:
                await upstream_resp.aclose()
                await client.aclose()

            return Response(
                content=content,
                status_code=upstream_resp.status_code,
                headers=resp_headers,
                media_type=content_type,
            )
    except httpx.RequestError as e:
        await client.aclose()
        error_msg = f"Network error proxying to {target_base}{path}: {e}"
        logger.error(error_msg, exc_info=True)
        return JSONResponse(status_code=502, content={"detail": f"Bad Gateway: {e.__class__.__name__} - {str(e)}"})
    except Exception as e:
        await client.aclose()
        error_msg = f"Unexpected error proxying to {target_base}{path}: {e}"
        logger.error(error_msg, exc_info=True)
        return JSONResponse(status_code=500, content={"detail": f"Internal Gateway Server Error: {e.__class__.__name__} - {str(e)}"})


async def _proxy_docs(docs_path: str, openapi_path: str,
                      target_base: str, prefix: str, request: Request) -> Response:
    """Проксирует Swagger UI и подменяет openapi.json URL для корректного отображения."""
    try:
        resp = await _fetch(docs_path, target_base, request)
        html = resp.text
        html = html.replace(
            f"url: '{openapi_path}'",
            f"url: '/{prefix}{openapi_path}'"
        )
        return HTMLResponse(content=html, status_code=resp.status_code)
    except Exception as e:
        error_msg = f"Error proxying docs for {target_base}{docs_path}: {e}"
        logger.error(error_msg, exc_info=True)
        return JSONResponse(status_code=502, content={"detail": f"Docs Gateway Error: {e.__class__.__name__} - {str(e)}"})
