# SKALD Engine Backend

A high-performance platform for interactive storytelling and role-playing games featuring AI characters. Built with a Vertical Slices (Domain-Driven Design) architecture for scalability and production use.

## Architecture

This project consists of two FastAPI microservices sharing a single PostgreSQL database:

### Auth Service (port 5000 — main webview)
- Handles authentication, user profiles, and JWT token management
- Located at `services/auth_service/`
- Exposes `/api/v1/auth` and `/api/v1/users` endpoints
- Swagger UI available at `/docs`

### Core Service (port 8000 — background console)
- Main game engine: AI character interactions, RAG, chat, lorebooks, personas, scenarios
- Located at `services/core_service/`
- Exposes all game-related endpoints under `/api/v1/`
- Swagger UI available at `/docs`
- Serves uploaded files (avatars, cards) at `/static/`

## Tech Stack

- **Language:** Python 3.12
- **Web Framework:** FastAPI with Uvicorn (ASGI)
- **Database:** PostgreSQL with pgvector extension (single Replit DB shared by both services)
- **ORM:** SQLAlchemy (async) with asyncpg driver
- **Migrations:** Alembic (separate version tables: `alembic_version_auth`, `alembic_version_core`)
- **AI/LLM:** Polza.ai (OpenAI-compatible wrapper) for character responses and embeddings
- **Auth:** JWT via python-jose, password hashing via passlib/bcrypt

## Project Structure

```
services/
  auth_service/      # Authentication microservice
    app/
      domains/user/  # User models, auth, JWT
      core/config.py # Settings (reads AUTH_DATABASE_URL)
    alembic/         # DB migrations
  core_service/      # Game engine microservice
    app/
      domains/       # character, chat, lorebook, persona, scenario
      core/          # RAG, prompt pipelines, director, stats
    alembic/         # DB migrations
shared/              # Common base classes and schemas used by both services
start_auth.sh        # Startup script for auth service (sets PYTHONPATH)
start_core.sh        # Startup script for core service (sets PYTHONPATH)
```

## Environment Variables

| Variable | Description |
|---|---|
| `SECRET_KEY` | JWT signing secret |
| `ALGORITHM` | JWT algorithm (default: HS256) |
| `AUTH_DATABASE_URL` | asyncpg URL for auth service DB |
| `CORE_DATABASE_URL` | asyncpg URL for core service DB |
| `POLZA_API_KEY` | Polza.ai / OpenAI-compatible API key (secret) |
| `POLZA_CHAT_MODEL` | Model for character chat responses |
| `POLZA_EMBEDDING_MODEL` | Model for vector embeddings |
| `POLZA_SUMMARY_MODEL` | Model for summarization |
| `POLZA_TITLE_MODEL` | Model for title generation |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiry |

## Running Locally

Both services need `PYTHONPATH` set to the workspace root so the `shared` module resolves:

```bash
# Auth service
bash start_auth.sh

# Core service  
bash start_core.sh
```

## Database Migrations

```bash
# Auth service
cd services/auth_service
AUTH_DATABASE_URL="..." SECRET_KEY="..." python3 -m alembic upgrade head

# Core service
cd services/core_service
CORE_DATABASE_URL="..." SECRET_KEY="..." POLZA_API_KEY="..." python3 -m alembic upgrade head
```

## Workflows

- **Start application** — Auth service on port 5000 (webview)
- **Core Service** — Core game engine on port 8000 (console)
