# Бэкенд SKALD Engine

Высокопроизводительная платформа для интерактивного сторителлинга и ролевых игр с ИИ-персонажами. Построена на архитектуре вертикальных срезов (Domain-Driven Design / Vertical Slices) с разделением на микросервисы и единый шлюз API Gateway.

## Архитектура системы

Проект состоит из трех сервисов и общего слоя:

### 1. API Gateway (порт 8080 / 8000)
- Единая точка входа для клиентов и фронтенда (Reverse Proxy на базе `httpx.AsyncClient`).
- Маршрутизация запросов к `auth_service` (`/api/v1/auth`, `/api/v1/users`) и `core_service` (все остальные эндпоинты `/api/v1/*`).
- Проксирование двунаправленного WebSocket-соединения (`/ws/updates`).
- Агрегированная документация Swagger UI:
  - Сводный индекс: `/docs`
  - Документация Auth Service: `/auth/docs`
  - Документация Core Service: `/core/docs`
- Антибуферизация SSE-стриминга (`X-Accel-Buffering: no`).

### 2. Auth Service (порт 8001)
- Микросервис аутентификации, регистрации, профилей пользователей и JWT.
- Расположен в `services/auth_service/`.
- Предоставляет эндпоинты `/api/v1/auth` и `/api/v1/users`.
- Собственная база данных `auth_db`.

### 3. Core Service (порт 8000)
- Основной игровой движок: ролевые диалоги, персонажи, сценарии, персоны игроков, лорбуки.
- 6-стадийный конвейер сборки контекста (`PromptPipeline`).
- Семантический поиск и эпизодическая память (гибридный RAG на `pgvector`).
- Режиссер сценариев (`DirectorService`) и генерация названий чатов.
- Расположен в `services/core_service/`.
- Собственная база данных `core_db` с поддержкой `pgvector`.

### 4. Shared Layer (`shared/`)
- Общие базовые классы `BaseRepository`, `BaseService`, `BaseController`.
- Единый формат ответа API `BaseResponse`.
- Централизованные схемы и конфигурация логирования.

---

## Технологический стек

- **Язык:** Python 3.12
- **Веб-фреймворк:** FastAPI + Uvicorn (ASGI)
- **База данных:** PostgreSQL с расширением `pgvector`
- **ORM:** SQLAlchemy (асинхронный движок с драйвером `asyncpg`)
- **Миграции:** Alembic (раздельные миграции для каждого сервиса)
- **ИИ / LLM:** Polza.ai (OpenAI-совместимый API) через единый системный токен
- **Безопасность:** JWT (python-jose), хеширование паролей (passlib/bcrypt)

---

## Структура проекта

```
gateway/             # Шлюз API Gateway (Reverse Proxy, WebSocket, Swagger)
services/
  auth_service/      # Микросервис аутентификации и пользователей
    app/
      domains/user/  # Модели, схемы, репозитории, сервисы и контроллеры пользователей
      core/config.py # Настройки (AUTH_DATABASE_URL, SECRET_KEY)
    alembic/         # Миграции базы данных auth_db
  core_service/      # Игровой движок и работа с LLM
    app/
      domains/       # character, chat, lorebook, persona, scenario
      core/          # PromptPipeline, RAG, Director, Stats, Title
    alembic/         # Миграции базы данных core_db
shared/              # Общие базовые абстракции и схемы ответа
```

---

## Переменные окружения

| Переменная | Описание |
|---|---|
| `SECRET_KEY` | Секретный ключ для подписи токенов JWT |
| `ALGORITHM` | Алгоритм подписи JWT (по умолчанию `HS256`) |
| `AUTH_DATABASE_URL` | URL подключения к базе данных auth_service (`postgresql+asyncpg://...`) |
| `CORE_DATABASE_URL` | URL подключения к базе данных core_service (`postgresql+asyncpg://...`) |
| `POLZA_API_KEY` | Системный API-ключ Polza.ai / OpenAI для генерации ответов и эмбеддингов |
| `POLZA_CHAT_MODEL` | Имя модели для диалогов персонажей |
| `POLZA_EMBEDDING_MODEL` | Имя модели для векторных эмбеддингов |
| `POLZA_SUMMARY_MODEL` | Имя модели для саммаризации памяти |
| `POLZA_TITLE_MODEL` | Имя модели для генерации заголовков чатов |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Срок жизни access токена в минутах |

---

## Запуск миграций базы данных

```bash
# Миграции Auth Service
cd services/auth_service
python -m alembic upgrade head

# Миграции Core Service
cd services/core_service
python -m alembic upgrade head
```

---

## Тестирование

```bash
# Тесты Gateway
python -m pytest gateway/tests

# Тесты Auth Service
python -m pytest services/auth_service/tests/test_auth_service.py

# Тесты Core Service
python -m pytest services/core_service/tests
```
