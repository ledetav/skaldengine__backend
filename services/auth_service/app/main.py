from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.domains.user.auth_router import router as auth_router
from shared.logging_config import setup_logging
from shared.middlewares.logging_middleware import LoggingMiddleware, add_global_exception_handler

setup_logging(settings.LOG_LEVEL)
from app.domains.user.router import router as user_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)
add_global_exception_handler(app)

app.include_router(auth_router, prefix=settings.API_V1_STR + "/auth", tags=["auth"])
app.include_router(user_router, prefix=settings.API_V1_STR + "/users", tags=["users"])

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "auth-service"}

@app.get("/")
def health_check():
    return {"status": "ok", "service": "auth-service"}