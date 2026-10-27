"""Системные эндпоинты API Gateway.

Включает проверку работоспособности шлюза и мониторинг доступности микросервисов.
"""
from fastapi import APIRouter
import httpx

from gateway.config import AUTH_BASE, CORE_BASE

router = APIRouter()


@router.get("/health")
def health():
    """Проверка базовой доступности самого API Gateway."""
    return {"status": "ok", "service": "gateway"}


@router.get("/debug/health")
async def debug_health():
    """Проверка доступности связанных микросервисов auth и core."""
    results = {}
    for name, base in [("auth", AUTH_BASE), ("core", CORE_BASE)]:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"{base}/health")
                results[name] = {"status": "ok", "http_status": r.status_code, "url": base}
        except httpx.ConnectError:
            results[name] = {"status": "unreachable", "error": "Connection refused — service is down", "url": base}
        except Exception as e:
            results[name] = {"status": "error", "error": str(e), "url": base}
    overall = "ok" if all(v["status"] == "ok" for v in results.values()) else "degraded"
    return {"gateway": "ok", "services": results, "overall": overall}


@router.get("/")
def root():
    """Корневой информационный эндпоинт со ссылками на документацию сервисов."""
    return {
        "status": "ok",
        "service": "skald-engine",
        "docs": {
            "auth": "/auth/docs",
            "core": "/core/docs",
        }
    }
