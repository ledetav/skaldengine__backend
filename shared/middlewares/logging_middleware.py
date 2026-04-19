import logging
import time
from fastapi import Request, FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        # Log request
        logger.info(f"Received request: {request.method} {request.url.path}")
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            # Log response
            logger.info(f"Completed request: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.4f}s")
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"Failed request: {request.method} {request.url.path} - Exception: {e} - Time: {process_time:.4f}s", exc_info=True)
            raise e

def add_global_exception_handler(app: FastAPI):
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception during {request.method} {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"}
        )
