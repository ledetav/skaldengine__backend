from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.domains.user.auth_router import router as auth_router
from app.domains.user.router import router as user_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=settings.API_V1_STR + "/auth", tags=["auth"])
app.include_router(user_router, prefix=settings.API_V1_STR + "/users", tags=["users"])

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "auth-service"}

@app.get("/")
def health_check():
    return {"status": "ok", "service": "auth-service"}