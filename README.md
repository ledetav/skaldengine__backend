# SKALDEngine Backend

**SKALD Engine** — high-performance platform for interactive storytelling and roleplay with AI characters. Built with **Domain-Driven Design (Vertical Slices)** and optimized for scalability and production readiness.

## Architecture

The project uses **Vertical Slices**, where each business domain is isolated within its directory. All services share a common base logic in the root shared/ folder.

- **services/auth_service/**: Auth, JWT, and User Profiles.
- **services/core_service/**: Game Logic, Chats, AI Personas, RAG, and Lorebooks.
- **shared/**: Global base classes for Repositories, Services, and Controllers.

---

## Production Deployment (Docker)

The project is configured for a unified deployment where both services run in a single container behind an Nginx reverse proxy.

### 1. Configure Environment
Create a .env file in the root directory based on .env.example:
```bash
cp .env.example .env
```
Fill in the required variables (especially SECRET_KEY and POLZA_API_KEY).

### 2. Build and Run
```bash
docker compose up -d --build
```
This will:
- Build the unified image (Python 3.11-slim).
- Start PostgreSQL instances for both services.
- Start the application container (Exposed on port 8000).

### 3. API Access Points
- **Unified Gateway**: http://localhost:8000/api/v1
- **Auth Endpoints**: /api/v1/auth/..., /api/v1/users/...
- **Core Endpoints**: /api/v1/chats/..., /api/v1/personas/..., etc.
- **Static Files (Uploads)**: http://localhost:8000/static/

---

## Manual Development Setup

If you need to run services separately without Docker:

### 1. Setup Database
Ensure you have two PostgreSQL databases (e.g., auth_db on 5432 and core_db on 5433).

### 2. Environment
Both services read configuration from the root .env file.
Ensure AUTH_DATABASE_URL and CORE_DATABASE_URL are set in the root .env.

### 3. Run Services
**Auth Service:**
```bash
cd services/auth_service
pip install -r requirements.txt
python -m alembic upgrade head
uvicorn app.main:app --reload --port 8001
```

**Core Service:**
```bash
cd services/core_service
pip install -r requirements.txt
python -m alembic upgrade head
uvicorn app.main:app --reload --port 8002
```

## Documentation
Detailed API documentation with all endpoints, models, and security roles:
👉 [API Documentation](api_documentation.md)
