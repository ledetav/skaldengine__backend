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

## Подробная документация API Core Service

### 1. Персоны Пользователя (`/api/v1/personas`) [Auth]

#### `GET /`
**Назначение:** Получение списка всех персон (аватаров) текущего пользователя.
- **Принимает:** Параметры пагинации `skip` (int), `limit` (int).
- **Возвращает:** Список объектов `UserPersona`.

#### `POST /`
**Назначение:** Создание новой персоны. Лимиты: 5 (User), 10 (Moderator), 15 (Admin).
- **Принимает:** `UserPersonaCreate` (JSON)
  - `name`: string (имя персонажа, обязательно)
  - `description`: string (краткое описание, опционально)
  - `avatar_url`: string (URL аватарки, опционально)
  - `age`: integer (возраст, опционально)
  - `appearance`: string (описание внешности, опционально)
  - `personality`: string (описание характера, опционально)
  - `gender`: string (пол: мужской, женский, иной, опционально)
  - `facts`: string (биография, лор, род деятельности, опционально)
- **Возвращает:** Созданную персону с ID.
- **Пример ввода:**
  ```json
  {
    "name": "Aragor",
    "description": "The true king of Gondor",
    "avatar_url": "https://example.com/aragor.jpg",
    "age": 35,
    "appearance": "Tall, dark hair, scarred face",
    "personality": "Stoic and brave",
    "facts": "Exiled from his homeland"
  }
  ```

#### `GET /{id}`
**Назначение:** Получить детальную информацию о конкретной персоне.
- **Возвращает:** Объект `UserPersona` (включая `owner_id` и `created_at`).

---

### 2. ИИ-Персонажи (`/api/v1/characters`) [Auth]

#### `GET /`
**Назначение:** Просмотр списка публичных персонажей, доступных для общения.
- **Принимает:** Параметры пагинации `skip`, `limit`.
- **Возвращает:** Список активных персонажей.

#### `GET /{id}`
**Назначение:** Получить полную биографию и настройки конкретного персонажа.
- **Возвращает:** Объект `Character` (детальные данные для промпта и UI).
- **Пример ответа:**
  ```json
  {
    "id": "aa3e4567-e89b-12d3-a456-426614174003",
    "creator_id": "123e4567-e89b-12d3-a456-426614174001",
    "name": "Eldritch",
    "description": "An ancient being of cosmic horror.",
    "fandom": "Cthulhu Mythos",
    "avatar_url": "https://example.com/avatar.jpg",
    "card_image_url": "https://example.com/card.jpg",
    "appearance": "Tentacles forming a spectral mass",
    "personality": "Unfathomable, cold, indifferent",
    "gender": "другое",
    "nsfw_allowed": true,
    "total_chats_count": 1250,
    "monthly_chats_count": 450,
    "scenarios_count": 8,
    "scenario_chats_count": 420,
    "is_public": true
  }
  ```

---

### 3. Реалтайм-обновления (Broadcast / WebSockets)

Для получения мгновенных уведомлений об изменениях в мире (новые персонажи, обновления, удаления) используйте WebSocket-подключение.

#### `WS /api/v1/ws/updates`
**Назначение:** Стриминг системных событий.
- **События (JSON):**
  - `{"type": "NEW_CHARACTER", "data": {...}}` — создан новый персонаж.
  - `{"type": "UPDATE_CHARACTER", "data": {...}}` — данные персонажа изменены (статистика, описание и т.д.).
  - `{"type": "DELETE_CHARACTER", "data": {"id": "..."}}` — персонаж удален.

---

### 4. Лорбуки (`/api/v1/lorebooks`) [Auth]

#### `GET /`
**Назначение:** Список лорбуков (баз знаний мира).
- **Доступ:** Обычным пользователям видны только их персональные лорбуки. Глобальный лор (персонажей/мира) доступен только админам/модераторам.
- **Принимает:** Фильтры `character_id` (UUID), `fandom` (string) — только для админов/модераторов.
- **Возвращает:** Список лорбуков со вложенными записями (`entries`) и полем `entries_count` (количество фактов).

#### `POST /`
**Назначение:** Создание нового контейнера знаний. Лимиты на персону: 3 (User), 5 (Moderator), 7 (Admin).
- **Принимает:** `LorebookCreate` (JSON)
  - `name`: string (название)
  - `description`: string (описание, опционально)
  - `user_persona_id`: UUID (привязка к своей персоне)
  - `character_id`: UUID (для лорбука персонажа, только для админов)
  - `fandom`: string (глобальный лор фандома, только для админов)
- **Возвращает:** Созданный лорбук.

#### `POST /{id}/entries`
**Назначение:** Добавление факта в лорбук.
- **Принимает:** `LorebookEntryCreate` (JSON)
  - `keywords`: string[] (ключевые слова для триггера RAG)
  - `content`: string (текст лорной записи)
  - `priority`: integer (приоритет вставки в контекст)
- **Возвращает:** Созданную запись.
- **Пример ввода:**
  ```json
  {
    "keywords": ["магия", "заклинание"],
    "content": "Магия черпается из эфира вокруг заклинателя.",
    "priority": 10
  }
  ```

---

### 5. Чаты (`/api/v1/chats`) [Auth]

#### `POST /`
**Назначение:** Инициализация новой игровой сессии (чата).
- **Принимает:** `ChatCreate` (JSON)
  - `character_id`: UUID (собеседник)
  - `user_persona_id`: UUID (выбранный аватар пользователя)
  - `scenario_id`: UUID (опционально, для сюжетных линий)
  - `persona_lorebook_id`: UUID (выбранный личный лорбук персоны, опционально)
  - `is_acquainted`: boolean (знакомы ли персонажи по сюжету, default: false)
  - `relationship_dynamic`: string (краткое описание динамики отношений)
  - `language`: string ("ru", "en", default: "ru")
  - `narrative_voice`: string ("first", "second", "third", default: "third")
  - `checkpoints_count`: integer (2-6, количество сюжетных целей)
- **Возвращает:** Объект чата с `id`, `mode` ("sandbox"/"scenario") и метаданными.
- **Пример ввода:**
  ```json
  {
    "character_id": "aa3e4567-...",
    "user_persona_id": "aa3e4567-...",
    "scenario_id": "550e8400-...",
    "is_acquainted": true,
    "relationship_dynamic": "Вынужденные напарники, не доверяющие друг другу.",
    "language": "ru",
    "narrative_voice": "third",
    "checkpoints_count": 4
  }
  ```

#### `GET /{id}/history`
**Назначение:** Получение полной истории переписки и состояния сценария.
- **Возвращает:** JSON-структуру с данными для отрисовки чата и дерева веток.
  - `active_leaf_id`: UUID (конец текущей выбранной ветки).
  - `active_branch`: list (линейный список сообщений от начала до текущего момента).
  - `tree`: list (плоский список ВСЕХ сообщений чата со всеми альтернативными ветками).
  - `checkpoints`: list (список целей сценария и их статус).
- **Метаданные сообщения (в `tree` и `branch`):**
  - `siblings_count`: количество альтернативных ответов на том же уровне (для свайп-индикатора).
  - `current_sibling_index`: порядковый номер текущего ответа (1-indexed).
  - `children_ids`: список ID прямых ответов на это сообщение.
- **Пример ответа:**
  ```json
  {
    "active_leaf_id": "uuid-msg-101",
    "active_branch": [
      { "id": "uuid-1", "role": "user", "content": "Привет!", "siblings_count": 1, "current_sibling_index": 1 },
      { "id": "uuid-101", "role": "assistant", "content": "Здравствуй, путник.", "siblings_count": 2, "current_sibling_index": 1 }
    ],
    "tree": [ 
       {"id": "uuid-1", "role": "user", "content": "Привет!", "children_ids": ["uuid-101", "uuid-102"]},
       {"id": "uuid-101", "role": "assistant", "content": "Здравствуй...", "parent_id": "uuid-1", "siblings_count": 2, "current_sibling_index": 1},
       {"id": "uuid-102", "role": "assistant", "content": "Кто ты?", "parent_id": "uuid-1", "siblings_count": 2, "current_sibling_index": 2}
    ],
    "checkpoints": [
      { "id": "uuid-cp-1", "order_num": 1, "goal_description": "Познакомиться", "is_completed": true }
    ]
  }
  ```

---

### 6. Сообщения (`/api/v1/messages`) [Auth]

#### `POST /chats/{chat_id}/messages/stream`
**Назначение:** Отправка сообщения и стриминг ответа ИИ в реальном времени.
- **Принимает:** `MessageCreate` (JSON)
  - `content`: string (текст вашего сообщения, обязательно).
  - `parent_id`: UUID (id сообщения, на которое отвечаем. Если пусто — ответ идет на последнее в активной ветке).
- **Возвращает:** SSE (Server-Sent Events) поток.
- **События (SSE):**
  - `message_id`: ID созданного сообщения (отправляется первым).
  - `token`: Текстовый чанк ответа (инкрементально).
  - `done`: Сигнал об успешном завершении генерации.
- **Формат ответа (SSE):**
  ```text
  event: message_id
  data: {"id": "uuid-..."}

  event: token
  data: {"text": "Привет,"}

  event: token
  data: {"text": " как дела?"}

  event: done
  data: {"status": "success"}
  ```

#### `PUT /messages/{id}`
**Назначение:** Редактирование текста (Непрямое ветвление).
- **Принимает:** `MessageEdit` (JSON)
  - `new_content`: string (новый текст).
- **Возвращает:** Новое сообщение.
- **Логика:** Оригинал сообщения остается в БД. Новое сообщение создается «рядом», позволяя переключаться между ними в истории (свайпы).

#### `POST /messages/{id}/fork`
**Назначение:** Явное ветвление (Создание параллельной линии в новом чате).
- **Принимает:** Ничего.
- **Возвращает:** Новый объект `Chat` (отдельную сессию-клон).
- **Логика (Параллельные миры):** 
  - Это действие создает **копию** вашего чата, ограниченную выбранным сообщением.
  - **Оригинальный чат не меняется** и его можно продолжать отдельно.
  - В новый чат переносятся только те сообщения, факты памяти (RAG) и прогресс сценария, которые были актуальны на момент выбранного сообщения.
  - Это позволяет создать "сохранение" в определенной точке и пойти по другому пути, не теряя основную историю.

#### `POST /messages/{parent_id}/regenerate/stream`
**Назначение:** Регенерация ответа ИИ ("Свайп") без изменения вашего текста.
- **Логика:** Создает альтернативный ответ ИИ от указанного сообщения пользователя. Создает новую непрямую ветку (внутри существующего чата), изолированную от предыдущего ответа ИИ.
- **Возвращает:** SSE поток (см. формат выше).

---

### 7. Пользовательские данные в контексте

Благодаря интеграции с **Auth Service**, каждый запрос содержит расширенную информацию о пользователе. В любом месте кода через `current_user` доступны:
- `current_user.id` (UUID)
- `current_user.login` (Логин)
- `current_user.username` (Публичный @handle)
- `current_user.full_name` (ФИО/Имя пользователя)
- `current_user.role` (Роль: admin, moderator, user)
- `current_user.birth_date` (Дата рождения)

---

### 8. Сценарии (`/api/v1/scenarios`) [Auth]

#### `GET /`
**Назначение:** Получение списка доступных сценариев (краткий).
- **Принимает:** Опциональный query-параметр `character_id`.
- **Возвращает:** Список (array) объектов `ScenarioShort`.
- **Пример ответа:**
  ```json
  [
    {
      "id": "uuid-scenario-1",
      "character_id": "uuid-char-1",
      "title": "Ночная встреча в таверне",
      "location": "Таверна 'Гордый единорог'",
      "description": "Вы оказываетесь втянуты в заговор, подслушав разговор..."
    }
  ]
  ```

#### `GET /{id}`
**Назначение:** Детальная информация о конкретном сценарии.
- **Доступ:** ТОЛЬКО Админы и Модераторы.
- **Возвращает:** Полный объект `Scenario` (включая стартовую и конечную точки).
- **Пример ответа:**
  ```json
  {
    "id": "uuid-scenario-1",
    "character_id": "uuid-char-1",
    "title": "Ночная встреча в таверне",
    "location": "Таверна 'Гордый единорог'",
    "description": "...",
    "gender": "male",
    "nsfw": false,
    "chats_count": 150,
    "start_point": "Вы сидите за дальним столом, когда вошедший рыцарь...",
    "end_point": "Вам необходимо выбраться из города до рассвета."
  }
  ```

---

### 9. Статистика и планировщики (Stats Service)

В сервисе работает `StatsService`, который отвечает за:
- Инкремент `total_chats_count` при каждом новом чате.
- Сброс и сохранение `monthly_chats_count` первого числа каждого месяца.
- Обеспечение актуальности данных для каталога персонажей.