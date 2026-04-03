# SKALDEngine Backend

**SKALD Engine** — это высокопроизводительная платформа для интерактивного сторителлинга и ролевой игры с ИИ-персонажами. Архитектура построена на микросервисах, продвинутом RAG (Retrieval Augmented Generation) на базе **pgvector** и гибридной системе памяти.

## ✨ Особенности

- **Иммерсивный ролеплей:** Глубокое погружение благодаря динамическим системным промптам, стилизации под разные типы повествования (1-е, 2-е, 3-е лицо).
- **Два режима игры:**
  - **Песочница:** Свободное развитие истории без жестких рамок.
  - **Сценарий:** Прохождение по заданным сюжетам с AI-Супервизором, который контролирует ключевые чекпоинты (Chat Checkpoints).
- **Умная память (pgvector RAG):** 
  - **Эпизодическая память:** ИИ сжимает и запоминает важные факты диалога в векторном хранилище.
  - **Лорбуки (Lorebooks):** Глобальные знания о мире и персонажах, подгружаемые по ключевым словам.
- **Древовидная история (Branching):** Поддержка бесконечных веток развития событий (Swipe/Regenerate) благодаря хранению сообщений в виде дерева.
- **Система Персон:** Гибкая настройка игровых профилей пользователя (имя, возраст, внешность, навыки) для разных сценариев.

## 🛠 Технический стек

- **Backend:** Python 3.11+, FastAPI.
- **Базы данных:**
  - **PostgreSQL 15 + pgvector** — единое хранилище для данных, истории сообщений и векторных эмбеддингов.
  - **Redis 7** — брокер задач (ARQ) и кеширование.
- **ORM / Миграции:** SQLAlchemy 2.0 (Async), Alembic.
- **AI Models (Polza.ai / OpenAI Wrapper):**
  - **Main LLM:** Gemini 3 Flash Preview.
  - **Logic/Supervisor:** Gemini 3.1 Flsh Lite Preview.
  - **Embeddings:** OpenAI `text-embedding-3-small`.

## 🏗 Архитектура сервисов

| Сервис | Порт | Описание | База данных |
| :--- | :--- | :--- | :--- |
| **Auth Service** | `:8001` | Auth, JWT, профили пользователей | PostgreSQL (`auth_db`) |
| **Core Service** | `:8000` | Game Logic, Chats, RAG, Characters | PostgreSQL (`core_db`) + Redis |

## 🚀 Быстрый старт

### 1. Инфраструктура (Docker)
Запустите PostgreSQL с поддержкой векторов и Redis:

```bash
docker compose up -d
```

### 2. Настройка Auth Service
В отдельном терминале:

```bash
cd services/auth_service
# Настройка окружения (Linux/macOS)
python3 -m venv .venv && source .venv/bin/activate
# Настройка окружения (Windows)
# python -m venv .venv; .venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env  # copy .env.example .env для Windows
# Отредактируйте .env и вставьте POLZA_API_KEY и SECRET_KEY

python -m alembic upgrade head
uvicorn app.main:app --reload --port 8001
```

### 3. Настройка Core Service
В другом терминале:

```bash
cd services/core_service
# Настройка окружения (Linux/macOS)
python3 -m venv .venv && source .venv/bin/activate
# Настройка окружения (Windows)
# python -m venv .venv; .venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env  # copy .env.example .env для Windows
# Отредактируйте .env и вставьте POLZA_API_KEY и SECRET_KEY

python -m alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

## 📚 Документация API

- **Core Service:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Auth Service:** [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)

### Типовой сценарий начала игры:
1. Регистрация в Auth Service (`POST /auth/register`).
2. Авторизация в Swagger (Authorize) с полученным JWT-токеном.
3. Создание Персоны (`POST /personas`).
4. Создание Чата с выбранным персонажем (`POST /chats`).
5. Отправка сообщений (`POST /chats/{id}/messages`).
