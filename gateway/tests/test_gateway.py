import pytest
import httpx
from fastapi.testclient import TestClient
from gateway.main import app
import gateway.main as gw_main

_RealAsyncClient = httpx.AsyncClient


def test_gateway_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "gateway"}


def test_gateway_root():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "skald-engine"


@pytest.mark.asyncio
async def test_proxy_non_streaming():
    """Verify regular non-streaming responses are passed through properly."""
    async def handler(request: httpx.Request):
        return httpx.Response(200, json={"message": "ok"}, headers={"content-type": "application/json"})

    transport = httpx.MockTransport(handler)

    def mock_async_client(*args, **kwargs):
        kwargs["transport"] = transport
        return _RealAsyncClient(*args, **kwargs)

    gw_main.httpx.AsyncClient = mock_async_client

    try:
        from httpx import ASGITransport
        async with _RealAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.get("/api/v1/characters")
            assert res.status_code == 200
            assert res.json() == {"message": "ok"}
    finally:
        gw_main.httpx.AsyncClient = _RealAsyncClient


@pytest.mark.asyncio
async def test_proxy_sse_streaming():
    """Verify that SSE stream is returned as StreamingResponse with correct anti-buffering headers."""
    chunks = [
        b"event: token\ndata: {\"content\": \"Hello\"}\n\n",
        b"event: token\ndata: {\"content\": \" world\"}\n\n",
        b"event: done\ndata: {\"status\": \"success\"}\n\n",
    ]

    async def stream_handler(request: httpx.Request):
        async def generate_chunks():
            for c in chunks:
                yield c
        return httpx.Response(
            200,
            content=generate_chunks(),
            headers={"content-type": "text/event-stream"}
        )

    transport = httpx.MockTransport(stream_handler)

    def mock_async_client(*args, **kwargs):
        kwargs["transport"] = transport
        return _RealAsyncClient(*args, **kwargs)

    gw_main.httpx.AsyncClient = mock_async_client

    try:
        from httpx import ASGITransport
        async with _RealAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            async with ac.stream("POST", "/api/v1/chats/123/messages/stream", json={"content": "Hi"}) as res:
                assert res.status_code == 200
                assert "text/event-stream" in res.headers["content-type"]
                assert res.headers.get("x-accel-buffering") == "no"
                assert "no-cache" in res.headers.get("cache-control", "")

                received_body = b""
                async for chunk in res.aiter_bytes():
                    received_body += chunk

                assert b"Hello" in received_body
                assert b"world" in received_body
                assert b"done" in received_body
    finally:
        gw_main.httpx.AsyncClient = _RealAsyncClient


@pytest.mark.asyncio
async def test_proxy_upstream_error_502():
    """Verify network error returns 502 Bad Gateway."""
    async def error_handler(request: httpx.Request):
        raise httpx.ConnectError("Connection refused")

    transport = httpx.MockTransport(error_handler)

    def mock_async_client(*args, **kwargs):
        kwargs["transport"] = transport
        return _RealAsyncClient(*args, **kwargs)

    gw_main.httpx.AsyncClient = mock_async_client

    try:
        from httpx import ASGITransport
        async with _RealAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.get("/api/v1/characters")
            assert res.status_code == 502
            assert "Bad Gateway" in res.json()["detail"]
    finally:
        gw_main.httpx.AsyncClient = _RealAsyncClient
