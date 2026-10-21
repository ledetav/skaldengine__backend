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


def test_cors_origin_security_unit():
    """Unit tests for is_origin_allowed helper."""
    from gateway.main import is_origin_allowed
    suffixes = [".replit.dev", ".replit.app", "localhost", "127.0.0.1"]
    origins = ["https://custom.app"]

    # Allowed
    assert is_origin_allowed("http://localhost:3000", origins, suffixes) is True
    assert is_origin_allowed("http://127.0.0.1:8080", origins, suffixes) is True
    assert is_origin_allowed("https://my-app.replit.dev", origins, suffixes) is True
    assert is_origin_allowed("https://sub.my-app.replit.app", origins, suffixes) is True
    assert is_origin_allowed("https://custom.app", origins, suffixes) is True

    # Attack/Phishing vectors that should be REJECTED
    assert is_origin_allowed("https://attacker-localhost.com", origins, suffixes) is False
    assert is_origin_allowed("https://localhost.attacker.com", origins, suffixes) is False
    assert is_origin_allowed("https://fake127.0.0.1.org", origins, suffixes) is False
    assert is_origin_allowed("https://evil-replit.dev.attacker.com", origins, suffixes) is False
    assert is_origin_allowed("https://notreplit.dev", origins, suffixes) is False
    assert is_origin_allowed("", origins, suffixes) is False


def test_cors_middleware_preflight_security():
    """Test CORS preflight OPTIONS request rejects malicious origins."""
    client = TestClient(app)

    # Legitimate origin
    res_ok = client.options("/health", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET"
    })
    assert res_ok.status_code == 200
    assert res_ok.headers.get("access-control-allow-origin") == "http://localhost:3000"

    # Malicious substring origin
    res_evil = client.options("/health", headers={
        "Origin": "https://attacker-localhost.com",
        "Access-Control-Request-Method": "GET"
    })
    assert res_evil.status_code == 200
    assert "access-control-allow-origin" not in res_evil.headers
