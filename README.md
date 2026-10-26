# SKALDEngine Backend

**SKALD Engine** — высокопроизводительная платформа для интерактивного сторителлинга и ролевых игр с ИИ-персонажами. Архитектура построена на принципах **Vertical Slices (Domain-Driven Design)**, разделена на микросервисы и объединена через централизованный асинхронный шлюз **API Gateway**.

---

## Архитектура проекта

```
                         ┌─────────────────────────────────┐
                         │   Caddy (TLS / Reverse Proxy)   │
                         └────────────────┬────────────────┘
                                          │
                                          ▼
                         ┌─────────────────────────────────┐
                         │      Gateway (FastAPI: 8080)    │
                         └───────┬─────────────────┬───────┘
                                 │                 │
               ┌─────────────────┘                 └─────────────────┐
               ▼                                                     ▼
┌───────────────────────────────┐                   ┌───────────────────────────────┐
│  Auth Service (FastAPI: 8001) │                   │  Core Service (FastAPI: 8000) │
├───────────────────────────────┤                   ├───────────────────────────────┤
│ • Регистрация и JWT           │                   │ • AI-персонажи и сценарии     │
│ • Профили пользователей       │                   │ • Древовидные чаты и форки    │
│ • Роли (admin/moderator/user) │                   │ • Prompt Pipeline (6 стадий)  │
│ • Управление персоналом       │                   │ • Гибридный RAG & Лорбуки     │
└──────────────┬────────────────┘                   └───────────────┬───────────────┘
               ▼                                                    ▼
┌───────────────────────────────┐                   ┌───────────────────────────────┐
│     PostgreSQL (auth-db)      │                   │     PostgreSQL + pgvector     │
│          Порт: 5432           │                   │          Порт: 5433           │
└───────────────────────────────┘                   └───────────────────────────────┘
```

### Компоненты системы

1. **[gateway/](gateway/README.md)** (порт 8080):
   - Единая точка входа в систему (Reverse Proxy на базе `httpx.AsyncClient`).
   - Автоматическая маршрутизация запросов к `auth_service` (`/api/v1/auth`, `/api/v1/users`) и `core_service` (все остальные эндпоинты `/api/v1/*`).
   - Двунаправленный прокси WebSocket (`/ws/updates`).
   - Антибуферизация потоковых ответов LLM (SSE) для корректной передачи чанков через Caddy/Nginx (`X-Accel-Buffering: no`).
   - Агрегированная Swagger-документация: `/docs`, `/auth/docs`, `/core/docs`.
   - Подробнее: см. [Документацию Gateway](gateway/README.md).

2. **`services/auth_service/`** (порт 8001):
   - Авторизация, регистрация, управление JWT-токенами.
   - Профили пользователей, смена учетных данных, публичные хэндлы.
   - Административный доступ и управление ролями.

3. **`services/core_service/`** (порт 8000):
   - Игровой движок, диалоговые сессии, дерево сообщений (Swipe, Edit, Fork).
   - **[Prompt Pipeline](services/core_service/app/core/prompt_pipeline/README.md)**: 6-стадийный конвейер сборки контекста (`IdentityStage`, `LorebookStage`, `RAGStage`, `ScenarioStage`, `HistoryStage`, `AssemblerStage`).
   - **Гибридный RAG**: поиск по семантическому сходству в рекурсивном CTE дерева сообщений с временным затуханием (Hybrid Scoring).
   - **Лорбуки**: стемминг ключевых слов через Aho-Corasick + pgvector embeddings.
   - Режиссура сюжета (`DirectorService`) и генерация заголовков чатов.

4. **`shared/`**:
   - Базовые абстракции `BaseRepository`, `BaseService`, `BaseController`.
   - Единый формат ответа `BaseResponse`.
   - Централизованное логирование и обработчики исключений.

---

## Быстрый старт (Docker Compose)

### 1. Подготовка окружения
Скопируйте пример переменных окружения:
```bash
cp .env.example .env
```
Укажите в `.env` ключи:
- `SECRET_KEY` (секретный ключ JWT)
- `AUTH_PASSWORD` и `CORE_PASSWORD` (пароли к базам данных)
- `POLZA_API_KEY` (ключ к API моделей Polza.ai / OpenAI)

### 2. Сборка и запуск контейнеров
```bash
docker compose up --build -d
```

### 3. Применение миграций базы данных
```bash
make migrate-auth m="Actualize db structure"
make migrate-core m="Actualize db structure"
make upgrade-auth
make upgrade-core
```

### 4. Просмотр логов
```bash
docker compose logs -f
# или через make:
make logs
```

### Точки доступа:
- **Шлюз Gateway**: `http://localhost:8080/api/v1`
- **Документация Swagger Gateway**: `http://localhost:8080/docs`
- **Веб-интерфейс через Caddy**: `http://localhost` (HTTPS при настроенном домене)

---

## Локальная разработка без Docker

Если требуется запустить сервисы изолированно на локальной машине:

### 1. Требования к базе данных
Необходимо поднять два инстанса PostgreSQL с расширением `pgvector`:
- `auth_db`: порт `5432`
- `core_db`: порт `5433`

### 2. Запуск Auth Service
```bash
cd services/auth_service
pip install -r requirements.txt
python -m alembic upgrade head
uvicorn app.main:app --reload --port 8001
```

### 3. Запуск Core Service
```bash
cd services/core_service
pip install -r requirements.txt
python -m alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 4. Запуск Gateway
```bash
cd gateway
pip install -r requirements.txt
uvicorn main:app --reload --port 8080
```

---

## Тестирование

Тесты сервисов запускаются раздельно с использованием корневого конфигурационного файла `pytest.ini`:

```bash
# Тесты ядра (Core Service) — Prompt Pipeline, RAG, Director, Message Service, Uploads
pytest -c pytest.ini services/core_service/tests

# Тесты шлюза (Gateway) — Маршрутизация, CORS, SSE-стриминг, Websocket
pytest -c pytest.ini gateway/tests
```

---

## Документация API

Полная спецификация всех маршрутов, схем Pydantic, прав доступа и форматов потоковых SSE ответов:
👉 **[Полная документация API](api_documentation.md)**
