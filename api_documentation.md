# Документация API SKALDEngine

Данное руководство содержит полное описание всех доступных эндпоинтов, их HTTP-методов, схем запросов и ответов, уровней доступа и примеров использования.

---

## Архитектурный обзор

Бэкенд SKALDEngine построен на базе централизованного шлюза API Gateway и выделенных микросервисов:

1. **API Gateway (Единая точка входа)**: `http://localhost:8080/api/v1` (или через reverse-proxy Caddy по адресу `http://localhost/api/v1`).
   - Автоматически маршрутизирует запросы к `auth_service` и `core_service`.
   - Обеспечивает проксирование WebSocket, установку CORS-заголовков и антибуферизацию потоковых ответов SSE.
   - Swagger / OpenAPI документация:
     - Сводный индекс шлюза: `http://localhost:8080/docs`
     - Спецификация Auth Service: `http://localhost:8080/auth/docs`
     - Спецификация Core Service: `http://localhost:8080/core/docs`
2. **Auth Service**: `http://localhost:8001/api/v1` (Внутренний доступ). Обеспечивает авторизацию, управление пользователями и JWT-профили.
3. **Core Service**: `http://localhost:8000/api/v1` (Внутренний доступ). Игровой движок, конвейер сборки промптов, потоковая генерация ИИ, персонажи, персоны, лорбуки и сценарии.

### Стандартизированный формат ответа (BaseResponse)

Все эндпоинты REST API используют формат **JSON** и возвращают стандартизированную структуру `BaseResponse`:

```json
{
  "success": true,
  "data": { ... },
  "message": "Операция выполнена успешно",
  "error_code": null
}
```

В случае ошибки поле `success` равно `false`, поле `data` равно `null`, а поля `message` и `error_code` содержат описание возникшей ошибки.

---

## Уровни доступа и роли

В системе существует иерархия ролей пользователей. Пользователь с более высокой ролью имеет доступ ко всем эндпоинтам нижестоящих ролей:
1. **(All)**: Публичный доступ, авторизация не требуется.
2. **(User)**: Требуется авторизация (`user`, `moderator`, `admin`). Большинство эндпоинтов требуют заголовок:
   ```http
   Authorization: Bearer <access_token>
   ```
3. **(Admin, Moderator / Staff)**: Требуется авторизация и наличие роли `admin` или `moderator`.
4. **(Admin)**: Полный системный доступ только для роли `admin`.

---

# 1. Authentication & Users (Auth Service)

Базовый префикс маршрута: `/auth` и `/users`.

### POST `/auth/register` (All)
Создание нового аккаунта пользователя.

#### Список входных данных:

| Поле | Формат | Описание | Обязательное | Ввод |
| :--- | :--- | :--- | :--- | :--- |
| **email** | string | Электронная почта | Да | Вручную |
| **login** | string | Уникальный логин для входа | Да | Вручную |
| **username** | string | Публичный никнейм (@handle) | Да | Вручную |
| **full_name**| string | Имя и фамилия | Нет | Вручную |
| **password** | string | Пароль (мин. 8 символов) | Да | Вручную |
| **birth_date**| string | Дата рождения (YYYY-MM-DD) | Да | Вручную |

#### Пример ввода:
```json
{
  "email": "player@example.com",
  "login": "SuperPlayer2000",
  "username": "@Skaldik",
  "full_name": "Ivan Ivanov",
  "password": "StrongPassword123!",
  "birth_date": "1995-04-03"
}
```

#### Пример вывода:
```json
{
  "success": true,
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "player@example.com",
    "login": "SuperPlayer2000",
    "username": "Skaldik",
    "full_name": "Ivan Ivanov",
    "birth_date": "1995-04-03",
    "avatar_url": null,
    "cover_url": null,
    "role": "user",
    "created_at": "2026-03-27T10:00:00Z"
  },
  "message": "User registered successfully",
  "error_code": null
}
```

---

### POST `/auth/login` (All)
OAuth2-совместимая авторизация и получение JWT токена через форму (`application/x-www-form-urlencoded`).

#### Входные данные (Form Data):
- `username`: Логин пользователя (или email).
- `password`: Пароль пользователя.

#### Пример вывода:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1Ni...",
    "token_type": "bearer"
  }
}
```

---

### POST `/auth/login/json` (All)
Авторизация через стандартный JSON payload (`application/json`). Рекомендуется для SPA фронтенда.

#### Пример ввода:
```json
{
  "login": "SuperPlayer2000",
  "password": "StrongPassword123!"
}
```

#### Пример вывода:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1Ni...",
    "token_type": "bearer"
  }
}
```

---

### GET `/users/me` (User)
Получение полного профиля текущего авторизованного пользователя.

#### Пример вывода:
```json
{
  "success": true,
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "player@example.com",
    "login": "SuperPlayer2000",
    "username": "Skaldik",
    "full_name": "Ivan Ivanov",
    "birth_date": "1995-04-03",
    "avatar_url": "/static/avatars/user-123.png",
    "cover_url": "/static/covers/cover-123.png",
    "role": "user",
    "created_at": "2026-03-27T10:00:00Z"
  }
}
```

---

### PATCH `/users/me` (User)
Универсальное обновление профиля текущего пользователя (все поля опциональны).

#### Входные данные:
```json
{
  "email": "new_email@example.com",
  "login": "NewLogin",
  "username": "NewHandle",
  "full_name": "Ivan Petrov",
  "birth_date": "1995-04-03",
  "avatar_url": "/static/new_avatar.png",
  "cover_url": "/static/new_cover.png"
}
```

---

### Точечные эндпоинты обновления профиля (User)

- **GET `/users/me/login`** — возвращает `{"login": "..."}`.
- **GET `/users/me/username`** — возвращает `{"username": "..."}`.
- **PATCH `/users/me/login`** — принимает `{"login": "new_login"}`.
- **PATCH `/users/me/username`** — принимает `{"username": "new_handle"}`.
- **PATCH `/users/me/full-name`** — принимает `{"full_name": "New Name"}`.
- **PATCH `/users/me/email`** — принимает `{"email": "user@example.com"}`.
- **PATCH `/users/me/profile`** — принимает `{"avatar_url": "...", "cover_url": "..."}`.
- **POST `/users/me/password`** — сменяет пароль:
  ```json
  {
    "old_password": "CurrentPassword123!",
    "new_password": "NewStrongPassword456!"
  }
  ```
- **DELETE `/users/me`** — удаляет аккаунт текущего пользователя.

---

### Публичные профили пользователей

#### GET `/users/profile/{username}` (User)
Получение публичного профиля любого пользователя по его хэндлу (`@handle` или `handle`).

#### GET `/users/batch?ids=uuid1,uuid2` (User)
Пакетное получение публичных профилей пользователей по списку UUID, разделенных запятой.

---

### Управление пользователями (Admin / Moderator)

- **GET `/users/` (Admin, Moderator)**: Пагинированный список всех зарегистрированных пользователей (`skip: int = 0`, `limit: int = 20`).
- **DELETE `/users/{user_id}` (Admin, Moderator)**: Принудительное удаление пользователя администратором.
- **PATCH `/users/{user_id}/role` (Admin, Moderator)**: Изменение системной роли пользователя.
  ```json
  {
    "role": "moderator"
  }
  ```
  *(Допустимые значения: `user`, `moderator`, `admin`).*

---

# 2. Core Game Features (Core Service)

Базовый префикс маршрута: `/api/v1`

---

## AI Characters (`/characters`)

Управление персонажами для диалогов и сторителлинга.

### GET `/characters/` (User)
Получение каталога персонажей. Для обычных пользователей возвращаются только публичные (`is_public: true`), для администраторов и модераторов — все.

**Query-параметры:**
- `skip` (int, default: 0)
- `limit` (int, default: 20)

#### Выходные данные (`data`):
Массив объектов `CharacterRead`:
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Eldritch",
    "description": "An ancient being of cosmic horror.",
    "type": "fandom",
    "fandom": "Cthulhu Mythos",
    "avatar_url": "/static/eldritch.jpg",
    "card_image_url": "/static/eldritch_card.jpg",
    "is_public": true,
    "gender": "other",
    "age": "Immortal",
    "nsfw_allowed": true,
    "total_chats_count": 1250,
    "monthly_chats_count": 85,
    "creator_id": "123e4567-e89b-12d3-a456-426614174000",
    "scenarios_count": 2,
    "scenario_chats_count": 14,
    "lorebook_ids": ["987e6543-e89b-12d3-a456-426614174000"],
    "author": {
      "username": "Narrator",
      "avatar_url": "/static/author.jpg"
    }
  }
]
```

### GET `/characters/{id}` (User)
Детальная информация о персонаже. Для администраторов и модераторов ответ включает скрытые поля `appearance` и `personality` (`CharacterAdminRead`).

### POST `/characters/` (Admin, Moderator)
Создание нового персонажа сотрудником. Для модераторов действует проверка: поле `fandom` должно указывать на существующий лорбук фандома.

### PUT `/characters/{id}` (Admin, Moderator)
Обновление параметров персонажа.

### DELETE `/characters/{id}` (Admin, Moderator)
Мягкое удаление персонажа.

---

## User Personas (`/personas`)

Персоны пользователя определяют образ игрока (имя, предыстория, пол, возраст, характер), от лица которого ведется диалог.

### POST `/personas/` (User)
Создание новой персоны.

#### Входные данные:

| Поле | Формат | Описание | Обязательное |
| :--- | :--- | :--- | :--- |
| **name** | string | Имя персоны (до 200 симв.) | Да |
| **description**| string | Краткое описание (до 500 симв.) | Нет |
| **avatar_url** | string | Ссылка на аватар персоны | Нет |
| **age** | string | Возраст (строка, напр. "24" или "150 лет") | Нет |
| **gender** | string | Пол персоны (напр. "male", "female", "other") | Нет |
| **appearance** | string | Описание внешности (до 2000 симв.) | Нет |
| **personality**| string | Черты характера (до 2000 симв.) | Нет |
| **facts** | string | Факты предыстории (до 2000 симв.) | Нет |

#### Пример ввода:
```json
{
  "name": "Aragor",
  "description": "Exiled ranger and heir to the throne.",
  "avatar_url": "/static/aragor.jpg",
  "age": "35",
  "gender": "male",
  "appearance": "Tall, dark hair, scarred face",
  "personality": "Stoic and brave",
  "facts": "Exiled from his homeland, knows ancient dialects"
}
```

#### Пример вывода:
```json
{
  "success": true,
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174001",
    "owner_id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Aragor",
    "description": "Exiled ranger and heir to the throne.",
    "avatar_url": "/static/aragor.jpg",
    "age": "35",
    "gender": "male",
    "appearance": "Tall, dark hair, scarred face",
    "personality": "Stoic and brave",
    "facts": "Exiled from his homeland, knows ancient dialects",
    "lorebook_count": 0,
    "chat_count": 0,
    "created_at": "2026-03-27T10:05:00Z"
  }
}
```

### GET `/personas/` (User)
Список всех персон текущего пользователя, включая агрегированные счетчики `lorebook_count` и `chat_count`.

### GET `/personas/{id}` (User)
Получение конкретной персоны по UUID.

### PATCH `/personas/{id}` (User)
Частичное обновление полей персоны.

### DELETE `/personas/{id}` (User)
Удаление персоны.

### GET `/personas/stats` (User)
Получение статистики активности текущего пользователя.

#### Пример вывода:
```json
{
  "success": true,
  "data": {
    "total_personas": 3,
    "total_lorebooks": 5,
    "total_chats": 12,
    "total_messages": 240
  }
}
```

---

## Chats (`/chats`)

Управление игровыми сессиями и диалогами с персонажами.

### POST `/chats/` (User)
Инициализация новой чат-сессии.

#### Входные данные:

| Поле | Формат | Описание | Обязательное |
| :--- | :--- | :--- | :--- |
| **character_id** | uuid | ID AI-персонажа | Да |
| **user_persona_id** | uuid | ID выбранной персоны игрока | Да |
| **scenario_id** | uuid | ID сценария (если игра идет по сюжету) | Нет |
| **title** | string | Пользовательское название чата | Нет |
| **is_acquainted** | boolean| Знакомы ли персонажи изначально (влияет на лорбук) | Нет (default: false) |
| **relationship_dynamic**| string| Динамика отношений ("rivals", "allies" и т.д.) | Нет |
| **custom_location** | string | Кастомная стартовая локация | Нет |
| **custom_plot_hook** | string | Кастомная завязка сюжета | Нет |
| **language** | string | Язык общения (напр. "ru", "en") | Нет (default: "ru") |
| **narrative_voice** | string | Стиль повествования ("first", "second", "third") | Нет (default: "third") |
| **persona_lorebook_id**| uuid | Дополнительный персональный лорбук персоны | Нет |
| **checkpoints_count** | int | Количество сюжетных точек (от 2 до 6) | Нет (default: 3) |

#### Пример вывода:
```json
{
  "success": true,
  "data": {
    "id": "789e0123-e89b-12d3-a456-426614174000",
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "character_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_persona_id": "123e4567-e89b-12d3-a456-426614174001",
    "scenario_id": null,
    "title": "Новое приключение",
    "is_acquainted": false,
    "relationship_dynamic": null,
    "language": "ru",
    "narrative_voice": "third",
    "persona_lorebook_id": null,
    "checkpoints_count": 3,
    "active_leaf_id": null,
    "mode": "roleplay",
    "created_at": "2026-03-27T10:10:00Z",
    "updated_at": null
  }
}
```

### GET `/chats/` (User)
Список активных чатов пользователя с обогащенными полями для интерфейса (`character_name`, `user_persona_name`, `last_message_preview`).

### GET `/chats/{chat_id}` (User)
Получение метаданных конкретного чата.

### PATCH `/chats/{chat_id}` (User)
Обновление параметров чата (`title`, `language`, `narrative_voice`, `is_acquainted`, `relationship_dynamic`, `persona_lorebook_id`, `active_leaf_id`).

### DELETE `/chats/{chat_id}` (User)
Удаление чата и связанных с ним сообщений.

### POST `/chats/{chat_id}/messages/stream` (User)
Отправка сообщения пользователем и получение ответа ИИ в виде SSE (Server-Sent Events) потока.

#### Входные данные:
```json
{
  "content": "Привет! Что ты знаешь о древней библиотеке?",
  "parent_id": "uuid-родительского-сообщения-или-null"
}
```

#### Потоковый ответ:
Ответ передается чанками `Content-Type: text/event-stream`. Внутренний блок размышлений модели `<Internal_Analysis>` передается в потоке и сохраняется в БД в поле `hidden_thought`.

### GET `/chats/{chat_id}/history` (User)
Получение древовидной истории сообщений чата (включая активную ветку и альтернативные свайпы).

---

## Message Operations (`/messages`)

Управление отдельными узлами дерева сообщений, форками и перегенерацией.

### POST `/messages/{parent_id}/regenerate/stream` (User)
Перегенерация ответа ИИ (Swipe). Генерирует альтернативную ветку от указанного родительского сообщения `parent_id` в потоковом режиме SSE.

### PUT `/messages/{message_id}` (User)
Редактирование текста сообщения. Создает новую ветку в дереве истории от указанной точки.

#### Входные данные:
```json
{
  "new_content": "Исправленный текст сообщения пользователя или персонажа."
}
```

### POST `/messages/{message_id}/fork` (User)
Явное ветвление чата. Создает **новую полноценную чат-сессию**, копируя цепочку истории сообщений от корня до указанного `message_id`.

#### Пример вывода:
```json
{
  "success": true,
  "data": {
    "new_chat_id": "333e4567-e89b-12d3-a456-426614174000",
    "message": "Chat successfully forked"
  }
}
```

### GET `/messages/{message_id}` (User)
Получение информации о конкретном сообщении (`id`, `chat_id`, `role`, `content`, `parent_id`, `hidden_thought`, `is_edited`, `created_at`).

### DELETE `/messages/{message_id}` (User)
Удаление сообщения из истории (доступно только владельцу чата).

---

## Lorebooks & Entries (`/lorebooks`)

Лорбуки представляют собой базы знаний о мире, фракциях, локациях, магии и персонажах. Записи лорбуков подмешиваются в контекст генерации через гибридный поиск (стемминг ключевых слов через Aho-Corasick + pgvector embeddings).

### Типы лорбуков (`type`):
- `fandom`: Системный лор вселенной (общий для персонажей фандома).
- `character`: Персональный лор конкретного AI-персонажа.
- `persona`: Персональный дневник/лор персоны игрока.

### POST `/lorebooks/` (User)
Создание нового лорбука.

#### Входные данные:
```json
{
  "name": "Хроники Альтерии",
  "type": "fandom",
  "fandom": "Alteria",
  "description": "Энциклопедия магии и древних королевств",
  "category": "general",
  "tags": ["магия", "эльфы", "академия"],
  "character_id": null,
  "user_persona_id": null
}
```

### GET `/lorebooks/` (User)
Список лорбуков с гибкой фильтрацией:
- `character_id` (UUID, optional)
- `persona_id` (UUID, optional)
- `user_id` (UUID, optional)
- `type` (string, optional)
- `skip` (int, default: 0)
- `limit` (int, default: 20)

### GET `/lorebooks/{lorebook_id}` (User)
Получить информацию о лорбуке и список его записей.

### PATCH `/lorebooks/{lorebook_id}` (User)
Обновление метаданных лорбука (`name`, `description`, `category`, `tags`, `fandom`).

### DELETE `/lorebooks/{lorebook_id}` (User)
Удаление лорбука.

---

### Lorebook Entries (Записи лорбука)

Запись содержит ключевые слова-триггеры, текст статьи, категорию и приоритет вставки.

#### POST `/lorebooks/{lorebook_id}/entries` (User)
Добавление одиночной записи в лорбук.

#### Входные данные:
```json
{
  "keywords": ["магия крови", "гемомантия"],
  "content": "Гемомантия — запрещенное искусство обращения к жизненной силе.",
  "priority": 15,
  "category": "magic",
  "is_always_included": false
}
```

#### POST `/lorebooks/{lorebook_id}/entries/bulk` (User)
Пакетное добавление сразу нескольких записей.
```json
{
  "entries": [
    {
      "keywords": ["орден рассвета"],
      "content": "Рыцарский орден, охраняющий границы святилища.",
      "priority": 10,
      "category": "factions"
    },
    {
      "keywords": ["хрустальный пик"],
      "content": "Высочайшая гора континента с залежами магических кристаллов.",
      "priority": 5,
      "category": "locations"
    }
  ]
}
```

#### GET `/lorebooks/{lorebook_id}/entries` (User)
Пагинированный список записей конкретного лорбука.
- `skip` (int, default: 0)
- `limit` (int, default: 20)
- `sort_by` (string, default: "created_at")

#### GET `/lorebooks/{lorebook_id}/entries/{entry_id}` (User)
Получение записи по ID.

#### PATCH `/lorebooks/{lorebook_id}/entries/{entry_id}` (User)
Редактирование записи (`keywords`, `content`, `priority`, `category`, `is_always_included`).

#### DELETE `/lorebooks/{lorebook_id}/entries/{entry_id}` (User)
Удаление записи из лорбука.

---

## Scenarios (`/scenarios`)

Сюжетные сценарии задают завязку, чекпоинты сюжета, начальную точку и целевую развязку.

### GET `/scenarios/` (User)
Список доступных сценариев.
- `character_id` (UUID, optional): Фильтр сценариев по персонажу.
- `skip` (int, default: 0)
- `limit` (int, default: 20)

### GET `/scenarios/{scenario_id}` (User)
Детальная информация о сценарии.

### POST `/scenarios/` (Admin, Moderator)
Создание нового сюжетного сценария.

#### Входные данные:
```json
{
  "title": "Побег из цитадели теней",
  "location": "Подземелья цитадели",
  "description": "Герои оказываются в темнице и должны совершить дерзкий побег.",
  "internal_description": "Стражники подкуплены повстанцами, но капитан стражи хранит верность лорду.",
  "start_point": "Сырая камера на нижнем ярусе тюрьмы.",
  "end_point": "Встреча с лодкой контрабандистов у тайного причала.",
  "character_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### PATCH `/scenarios/{scenario_id}` (Admin, Moderator)
Обновление полей сценария.

### DELETE `/scenarios/{scenario_id}` (Admin, Moderator)
Удаление сценария.

---

# 3. Administration & Utility

## Admin Characters (`/admin/characters`)
Расширенный доступ к персонажам с проверкой прав доступа.

- **POST `/admin/characters/`** (Admin, Moderator) — Создание персонажа от имени администратора.
- **PATCH `/admin/characters/{character_id}`** (Admin, Moderator) — Обновление полей персонажа.
- **DELETE `/admin/characters/{character_id}`** (Admin, Moderator) — Мягкое удаление персонажа.
- **POST `/admin/characters/{character_id}/images`** (Admin, Moderator) — Загрузка аватара и фоновой карточки (`multipart/form-data`: `avatar`, `card_image`).

## Admin Lorebooks (`/admin/lorebooks`)
Управление глобальными и персонажными базами знаний.

- **GET `/admin/lorebooks/check-fandom?name=...`** (Admin, Moderator) — Проверка наличия системного лорбука фандома.
- **POST `/admin/lorebooks/`** (Admin, Moderator) — Создание лорбука (Модераторам разрешено создавать только персонажные лорбуки с `character_id`).
- **PATCH `/admin/lorebooks/{lorebook_id}`** (Admin, Moderator) — Обновление метаданных лорбука.
- **DELETE `/admin/lorebooks/{lorebook_id}`** (Admin, Moderator) — Удаление лорбука.
- **POST `/admin/lorebooks/{lorebook_id}/entries`** (Admin, Moderator) — Добавление записи.
- **POST `/admin/lorebooks/{lorebook_id}/entries/bulk`** (Admin, Moderator) — Пакетное добавление записей.
- **GET `/admin/lorebooks/{lorebook_id}/entries`** (Admin, Moderator) — Получение записей с пагинацией (`items`, `total`).
- **PATCH `/admin/lorebooks/{lorebook_id}/entries/{entry_id}`** (Admin, Moderator) — Обновление записи.
- **DELETE `/admin/lorebooks/{lorebook_id}/entries/{entry_id}`** (Admin, Moderator) — Удаление записи.

## Utility Endpoints

### POST `/upload/` (User)
Загрузка медиа-файлов (изображений) для аватаров, карточек и лорбуков.
- Формат: `multipart/form-data` (`file`).
- Допустимые типы: `image/png`, `image/jpeg`, `image/gif`, `image/webp`.
- Ограничение по размеру: до 10 МБ.
- Валидация: проверка сигнатур magic bytes.

#### Пример ответа:
```json
{
  "url": "/static/a1b2c3d4-e5f6-7890-abcd-ef1234567890.webp"
}
```

### WebSocket `/ws/updates` (User)
Двунаправленный WebSocket канал для событий реального времени (статусы очередей генерации, уведомления системы, синхронизация сообщений).

---

# 4. Error Handling & Status Codes

Все ошибки возвращаются со стандартным HTTP кодом и JSON структурой `BaseResponse`:

```json
{
  "success": false,
  "data": null,
  "message": "Описание ошибки",
  "error_code": "RESOURCE_NOT_FOUND"
}
```

- **400 Bad Request**: Некорректные параметры запроса (например, неверный UUID, неподдерживаемый MIME-тип).
- **401 Unauthorized**: Заголовок `Authorization` отсутствует, просрочен или содержит невалидный JWT токен.
- **403 Forbidden**: Недостаточно прав для выполнения действия (например, попытка модератора изменить фандомный лорбук).
- **404 Not Found**: Запрашиваемый ресурс (персонаж, чат, лорбук, сообщение) не найден.
- **413 Payload Too Large**: Загружаемый файл превышает лимит 10 МБ.
- **422 Unprocessable Entity**: Ошибка валидации структуры Pydantic.
- **500 Internal Server Error**: Необработанная ошибка сервера.
