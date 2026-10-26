# SKALD Gateway (API & WebSocket Reverse Proxy)

Шлюз `gateway` выступает единой точкой входа (Reverse Proxy / API Gateway) для бэкенда SKALD Engine, объединяя микросервисы `auth_service` и `core_service`.

## Модульная архитектура

* **`main.py`** — Сборка приложения FastAPI, регистрация CORS-мидлвара, глобальный обработчик ошибок и маршрутизация общих API и WebSocket запросов.
* **`config.py`** — Базовые настройки окружения:
  * `AUTH_BASE_URL` (по умолчанию `http://127.0.0.1:8001`)
  * `CORE_BASE_URL` (по умолчанию `http://127.0.0.1:8000`)
  * `AUTH_PREFIXES` (`/api/v1/auth`, `/api/v1/users`)
* **`cors.py`** — Валидация Origin с защитой от спуфинга (`is_origin_allowed`) и динамическое `cors_middleware` (с поддержкой preflight `OPTIONS`).
* **`proxy.py`** — Проксирование HTTP-запросов и потоковых SSE-ответов (`_proxy`, `_fetch`, `_proxy_docs`):
  * Антибуферизация для обратных прокси Nginx / Caddy (`X-Accel-Buffering: no`, `Cache-Control: no-cache, no-transform`).
  * Бесконечный read timeout для потоковых ответов генерации текста.
* **`websocket.py`** — Двунаправленное проксирование WebSocket соединений (`websocket_proxy_handler`) с пересылкой токенов и заголовков.
* **`routers/`**:
  * **`system.py`** — Системные эндпоинты `/`, `/health`, `/debug/health` (проверка связи с микросервисами).
  * **`docs.py`** — Проксирование документации Swagger UI и схем OpenAPI (`/auth/docs`, `/core/docs`).
