# SkaldEngine Core Service

Основной микросервис игровой платформы. Отвечает за игровую логику, управление персонажами, сессиями, RAG (Retrieval Augmented Generation) и взаимодействие с LLM (Google Gemini).

## Технический стек

- Framework: FastAPI
- Database: PostgreSQL (Game Data)
- Vector DB: ChromaDB (Lore & Memory)
- AI: Google Gemini API (Models: 2.0 Flash / 3.0 Flash)
- Storage: Local / Static (Images)

## Авторизация

Сервис не хранит пароли пользователей и не имеет таблицы `users`.
Он доверяет JWT-токенам, подписанным **Auth Service**.

Как авторизоваться в Swagger UI:

1. Получите токен в **Auth Service** (`POST /auth/login`).
2. Скопируйте строку `access_token` (без кавычек).
3. Нажмите кнопку **Authorize** в Core Service Swagger.
3. Вставьте токен в поле `Value` и нажмите **Authorize**.

## Запуск и Настройка

1. Переменные окружения (`.env`)
```
PROJECT_NAME="Skald Core Service"
API_V1_STR="/api/v1"
SECRET_KEY="your-secret-key-shared-with-auth"
DATABASE_URL="postgresql+asyncpg://core_user:core_password@localhost:5433/core_db"
GEMINI_API_KEY="your-gemini-api-key"
CHROMA_DB_PATH="./chroma_db"
UPLOAD_DIR="./uploads"
```

2. Запуск

Сервис запускается на порту `8000`.

### Установка
`pip install -r requirements.txt`

### Миграции
`python -m alembic upgrade head`

### Старт
`uvicorn app.main:app --reload --port 8000`

## Основные Эндпоинты

Полный список доступен в Swagger: `http://localhost:8000/docs`

- Sessions (`/sessions`): Создание игры, чат с ИИ, история сообщений.
    - `POST /sessions/` — Начать игру (Сборка системного промпта).
    - `POST /sessions/{id}/chat` — Отправить сообщение (RAG + LLM Generation).
- Characters (`/characters`): CRUD для ИИ-персонажей.
- Personas (`/personas`): Управление профилями игрока (Кого отыгрывает юзер).
- Lore (`/lore`): База знаний персонажей (автоматически индексируется в ChromaDB).