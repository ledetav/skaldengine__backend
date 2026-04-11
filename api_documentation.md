# SkaldEngine API Documentation

Welcome to the SkaldEngine API documentation. This guide provides an exhaustive list of all endpoints, their methods, request/response formats, and examples.

## Overview

The SkaldEngine backend consists of two main microservices:
1. **Auth Service**: `http://localhost:8001/api/v1` - Authentication and user management.
2. **Core Service**: `http://localhost:8000/api/v1` - Main game logic and AI interactions.

All requests and responses use **JSON**. All responses follow this common structure:
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation successful",
  "error_code": null
}
```

## Уровни доступа и роли

В системе существует иерархия ролей. Пользователь с более высокой ролью имеет доступ ко всем эндпоинтам нижестоящих ролей:
1. **(All)**: Доступно всем, даже без токены.
2. **(User)**: Требуется авторизация. Доступно всем зарегистрированным пользователям, включая модераторов и админов.
3. **(Admin, Moderator)**: Требуется авторизация и наличие роли `admin` или `moderator`.

Большинство эндпоинтов требуют заголовок `Authorization: Bearer <token>`.

---

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
| **polza_api_key**| string | Личный API ключ Polza AI | Нет | Вручную |

#### Список выходных данных (внутри `data`):

| Поле | Формат | Описание | Обязательное | Генерация |
| :--- | :--- | :--- | :--- | :--- |
| **id** | uuid | Уникальный ID пользователя | Да | Автоматически |
| **email** | string | Электронная почта | Да | Из базы |
| **login** | string | Логин | Да | Из базы |
| **username** | string | Публичный никнейм | Да | Из базы |
| **full_name**| string | Имя и фамилия | Нет | Из базы |
| **role** | string | Роль (user/admin) | Да | Автоматически |
| **avatar_url**| string | Ссылка на аватар | Нет | Из базы |
| **cover_url** | string | Ссылка на обложку профиля | Нет | Из базы |
| **polza_api_key**| string | Личный API ключ Polza AI | Нет | Из базы |
| **created_at**| string | Дата создания профиля | Да | Автоматически |

#### Пример ввода:
```json
{
  "email": "user@example.com",
  "login": "SuperPlayer2000",
  "username": "@Skaldik",
  "full_name": "Ivan Ivanov",
  "password": "StrongPassword123!",
  "birth_date": "1995-04-03",
  "polza_api_key": "sk-polza-..."
}
```

#### Пример вывода:
```json
{
  "success": true,
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "login": "SuperPlayer2000",
    "username": "@Skaldik",
    "full_name": "Ivan Ivanov",
    "avatar_url": null,
    "cover_url": null,
    "birth_date": "1995-04-03",
    "polza_api_key": "sk-polza-...",
    "role": "user",
    "created_at": "2024-03-27T10:00:00Z"
  },
  "message": "User registered successfully",
  "error_code": null
}
```

---

### POST `/auth/login` (All)
Авторизация и получение JWT токена.

#### Список входных данных (Form Data):

| Поле | Формат | Описание | Обязательное | Ввод |
| :--- | :--- | :--- | :--- | :--- |
| **username** | string | Логин пользователя | Да | Вручную |
| **password** | string | Пароль | Да | Вручную |

#### Список выходных данных (внутри `data`):

| Поле | Формат | Описание | Обязательное | Генерация |
| :--- | :--- | :--- | :--- | :--- |
| **access_token** | string | JWT токен для авторизации | Да | Автоматически |
| **token_type** | string | Тип токена (bearer) | Да | Автоматически |

#### Пример ввода (как Form Data):
`username=SuperPlayer2000&password=StrongPassword123!`

#### Пример вывода:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbG...",
    "token_type": "bearer"
  }
}
```

---

### GET `/users/me` (User)
Получение информации о текущем авторизованном пользователе.

#### Список выходных данных (внутри `data`):
(Аналогично `/auth/register`, возвращает полную модель пользователя).

#### Пример вывода:
```json
{
  "success": true,
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "login": "SuperPlayer2000",
    "username": "@Skaldik",
    "full_name": "Ivan Ivanov",
    "avatar_url": "http://...",
    "cover_url": "http://...",
    "polza_api_key": "sk-polza-...",
    "role": "user"
  }
}
```

---

### PATCH `/users/me` (User)
Обновление профиля пользователя. Поддерживает частичное обновление всех основных полей.

#### Список входных данных:

| Поле | Формат | Описание | Обязательное |
| :--- | :--- | :--- | :--- |
| **email** | string | Электронная почта | Нет |
| **login** | string | Логин | Нет |
| **username** | string | Публичный никнейм | Нет |
| **full_name**| string | Имя и фамилия | Нет |
| **birth_date**| string | Дата рождения (YYYY-MM-DD) | Нет |
| **avatar_url**| string | Ссылка на аватар | Нет |
| **cover_url** | string | Ссылка на обложку профиля | Нет |
| **polza_api_key**| string | API ключ Polza AI | Нет |

---

### POST `/users/me/password` (User)
Смена пароля.

#### Список входных данных:

| Поле | Формат | Описание | Обязательное | Ввод |
| :--- | :--- | :--- | :--- | :--- |
| **old_password** | string | Текущий пароль | Да | Вручную |
| **new_password** | string | Новый пароль | Да | Вручную |

---

### DELETE `/users/me` (User)
Удаление учетной записи текущего пользователя.
(Не принимает данных, возвращает `success: true`).

---

## 2. Core Game Features (Core Service)

### AI Characters (`/characters`)
Доступ к списку и детальной информации об AI-персонажах.

#### GET `/characters/` (User)
Получить список всех публичных персонажей.

**Параметры (Query):**
- `skip` (int): Количество пропускаемых записей (по умолчанию 0).
- `limit` (int): Максимальное количество записей (по умолчанию 20).

**Пример вывода:**
```json
{
  "success": true,
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Eldritch",
      "description": "An ancient being of cosmic horror.",
      "fandom": "Cthulhu Mythos",
      "total_chats_count": 1250,
      "nsfw_allowed": true
    }
  ]
}
```

---

#### GET `/characters/{id}` (User)
Детальная информация об одном персонаже.

**Выходные данные (`data`):**

| Поле | Формат | Описание |
| :--- | :--- | :--- |
| **id** | uuid | ID персонажа |
| **name** | string | Имя |
| **description**| string | Описание |
| **fandom** | string | Фэндом |
| **avatar_url** | string | Ссылка на аватар |
| **appearance** | string | Описание внешности (**только Admin**) |
| **personality**| string | Описание личности (**только Admin**) |
| **nsfw_allowed**| boolean| Разрешен ли контент 18+ |

---

### User Personas (`/personas`)
Управление вашими игровыми личностями (персонами).

#### POST `/personas/` (User)
Создание новой персоны.

**Входные данные:**

| Поле | Формат | Описание | Обязательное | Ввод |
| :--- | :--- | :--- | :--- | :--- |
| **name** | string | Имя персоны | Да | Вручную |
| **description**| string | Краткое описание | Нет | Вручную |
| **age** | int | Возраст | Нет | Вручную |
| **gender** | string | Пол | Нет | Вручную |
| **appearance** | string | Описание внешности | Нет | Вручную |
| **personality**| string | Описание личности | Нет | Вручную |
| **facts** | string | Дополнительные факты | Нет | Вручную |

**Пример ввода:**
```json
{
  "name": "Aragor",
  "description": "Exiled ranger and heir to the throne.",
  "age": 35,
  "gender": "male",
  "appearance": "Tall, dark hair, scarred face",
  "personality": "Stoic and brave"
}
```

**Пример вывода:**
```json
{
  "success": true,
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174001",
    "name": "Aragor",
    "owner_id": "uuid-пользователя",
    "lorebook_count": 0,
    "chat_count": 0,
    "created_at": "2024-03-27T10:05:00Z"
  }
}
```

---

#### GET `/personas/` (User)
Список всех ваших персон.
(Возвращает массив объектов персон, включая `lorebook_count` и `chat_count`).

---

#### GET `/personas/stats` (User)
Получение агрегированной статистики текущего пользователя.

**Выходные данные (`data`):**

| Поле | Формат | Описание |
| :--- | :--- | :--- |
| **total_chats** | int | Общее количество чатов пользователя |
| **total_personas** | int | Общее количество созданных персон |
| **total_lorebooks**| int | Количество лорбуков (свои персоны + свои персонажи) |

**Пример вывода:**
```json
{
  "success": true,
  "data": {
    "total_chats": 12,
    "total_personas": 3,
    "total_lorebooks": 5
  }
}
```

---

#### PATCH `/personas/{id}` (User)
Частичное обновление персоны. Принимает те же поля, что и при создании, но все они необязательны.

---

#### DELETE `/personas/{id}` (User)
Удаление персоны.

### Chats (`/chats`)
Управление чат-сессиями и отправка сообщений.

#### POST `/chats/` (User)
Создание новой чат-сессии с AI-персонажем.

**Входные данные:**

| Поле | Формат | Описание | Обязательное | Ввод |
| :--- | :--- | :--- | :--- | :--- |
| **character_id** | uuid | ID AI-персонажа | Да | Выбор |
| **user_persona_id** | uuid | ID вашей персоны | Да | Выбор |
| **scenario_id** | uuid | ID сценария (если есть) | Нет | Выбор |
| **title** | string | Название чата | Нет | Вручную |
| **language** | string | Язык общения (напр. "ru", "en")| Нет | Выбор |
| **narrative_voice** | string | Повествование (first, second, third)| Нет | Выбор |

**Пример ввода:**
```json
{
  "character_id": "550e8400",
  "user_persona_id": "123e4567",
  "narrative_voice": "third",
  "language": "ru"
}
```

**Пример вывода:**
```json
{
  "success": true,
  "data": {
    "id": "uuid-нового-чата",
    "created_at": "2024-03-27T10:10:00Z"
  }
}
```

---

#### POST `/chats/{chat_id}/messages/stream` (User)
Отправка сообщения пользователем и получение потокового ответа AI.

**Входные данные:**

| Поле | Формат | Описание | Обязательное | Ввод |
| :--- | :--- | :--- | :--- | :--- |
| **content** | string | Текст сообщения | Да | Вручную |
| **parent_id** | uuid | ID родительского сообщения (для веток)| Нет | Авто |

**Вывод:** SSE-поток чанков. Каждый чанк — это JSON с текстом или метаданными.

---

#### GET `/chats/{chat_id}/history` (User)
Получение истории сообщений.

**Выходные данные (список `messages`):**

| Поле | Формат | Описание |
| :--- | :--- | :--- |
| **id** | uuid | ID сообщения |
| **role** | string | Роль (user/assistant) |
| **content** | string | Текст |
| **parent_id** | uuid | ID родителя (для построения дерева) |
| **hidden_thought**| string| Внутренние мысли AI (если есть) |

---

### Message Operations (`/messages`)

#### POST `/messages/{parent_id}/regenerate/stream` (User)
Перегенерация ответа (Swipe). Создает альтернативную ветку ответа для того же родительского сообщения.

#### PUT `/messages/{message_id}` (User)
Редактирование сообщения. Создает новую ветку истории от этого момента.

**Входные данные:**
- `content`: Новый текст сообщения.

#### GET `/messages/{message_id}` (User)
Получить информацию о конкретном сообщении.

#### DELETE `/messages/{message_id}` (User)
Удалить сообщение. Удаление возможно только если вы владелец чата.

### Lorebooks & Entries (`/lorebooks`)
Управление базами знаний (лорбуками) для контекста AI.

#### POST `/lorebooks/` (User)
Создание нового лорбука.

**Входные данные:**

| Поле | Формат | Описание | Обязательное | Ввод |
| :--- | :--- | :--- | :--- | :--- |
| **name** | string | Название лорбука | Да | Вручную |
| **character_id** | uuid | Привязка к персонажу | Нет | Выбор |
| **user_persona_id** | uuid | Привязка к персоне | Нет | Выбор |
| **fandom** | string | Фэндом | Нет | Вручную |
| **description**| string | Описание | Нет | Вручную |

**Пример вывода:**
```json
{
  "success": true,
  "data": {
    "id": "uuid-лорбука",
    "name": "Chronicles of Magic"
  }
}
```

---

#### POST `/lorebooks/{id}/entries` (User)
Добавление записи в лорбук.

**Входные данные:**

| Поле | Формат | Описание | Обязательное | Ввод |
| :--- | :--- | :--- | :--- | :--- |
| **keywords** | list[str]| Ключевые слова-триггеры | Да | Вручную |
| **content** | string | Текст записи | Да | Вручную |
| **priority** | int | Приоритет вставки в контекст| Нет | Вручную |

**Пример ввода:**
```json
{
  "keywords": ["magic", "spell"],
  "content": "Magic is drawn from the aether.",
  "priority": 10
}
```

#### GET `/lorebooks/entries/{entry_id}` (User)
Получить информацию о конкретной записи лорбука.

---

### Scenarios (`/scenarios`)
Управление игровыми сценариями.

#### GET `/scenarios/` (User)
Список сценариев. Может быть отфильтрован по `character_id`.

**Выходные данные (`data` - список):**

| Поле | Формат | Описание |
| :--- | :--- | :--- |
| **id** | uuid | ID сценария |
| **title** | string | Название |
| **location** | string | Локация |
| **description**| string | Описание завязки |

---

#### GET `/scenarios/{id}` (User)
Детальная информация о сценарии, включая стартовую и конечную точки.

---

## 3. Administration & Utility

### Роли и ограничения административной панели
1. **Admin**: Полный доступ ко всем эндпоинтам. Управление общесистемными лорбуками фандомов.
2. **Moderator**: Ограничен управлением контентом персонажей. Не может создавать/изменять общесистемные лорбуки фандомов (только персонажные). Создание персонажа модератором требует наличия существующего лорбука фандома.

### Admin Characters (`/admin/characters`)
Полный CRUD-доступ ко всем персонажам в системе.

#### POST `/admin/characters/` (Admin, Moderator)
Создание персонажа от имени администратора.

**Входные данные:**
(Аналогично схеме персонажа, включая поля `is_public`, `nsfw_allowed`).

> [!IMPORTANT]
> **Для модераторов**: При создании персонажа поле `fandom` должно соответствовать названию существующего лорбука фандома. Если такой лорбук отсутствует, запрос вернет ошибку 400.

---

#### POST `/admin/characters/{id}/images` (Admin, Moderator)
Загрузка аватара и фонового изображения для персонажа.

**Входные данные (`multipart/form-data`):**
- `avatar` (file): Картинка аватара.
- `card_image` (file): Фоновое изображение.

---

### Admin Lorebooks (`/admin/lorebooks`)
Управление базами знаний.

#### GET `/admin/lorebooks/check-fandom` (Admin, Moderator)
Проверить, существует ли системный лорбук для конкретного фандома.

**Параметры:**
- `name` (string): Название фандома.

**Пример вывода:**
```json
{
  "success": true,
  "data": { "exists": true }
}
```

#### POST `/admin/lorebooks/` (Admin, Moderator)
Создание лорбука. 
- **Admin**: Может создавать любые лорбуки.
- **Moderator**: Обязан передать `character_id`. Создание общих лорбуков фандомов запрещено.

#### PUT/DELETE `/admin/lorebooks/{id}` (Admin, Moderator)
- **Admin**: Полный доступ.
- **Moderator**: Изменение/удаление возможно только для лорбуков, привязанных к конкретному персонажу (`character_id != null`).

#### GET `/admin/lorebooks/entries/{id}` (Admin, Moderator)
Получить информацию о конкретной записи лорбука.

---

### Character Attributes (`/admin/attributes`)
Управление глобальными атрибутами персонажей (навыки, черты и т.д.).

**Методы:**
- **GET** `/admin/attributes/` (Admin, Moderator)
- **GET** `/admin/attributes/{attribute_id}` (Admin, Moderator)
- **POST** `/admin/attributes/bulk` (Admin, Moderator)

---

### Utility

#### POST `/upload/` (User)
Загрузка произвольных изображений (для лора, сценариев и т.д.).

**Входные данные (`multipart/form-data`):**
- `file` (file): Файл изображения.

**Пример вывода:**
```json
{
  "success": true,
  "data": {
    "url": "/static/uploads/uuid-name.png"
  }
}
```

---

#### WebSocket `/ws/updates` (User)
Поток событий реального времени. При подключении клиент начинает получать уведомления о статусе генерации, новых сообщениях и системных обновлениях.

---

## 4. Error Codes

- **401**: Токен отсутствует или невалиден.
- **403**: Доступ запрещен (недостаточно прав или вы не владелец ресурса).
- **404**: Запрашиваемый ресурс не найден.
- **422**: Ошибка валидации данных (проверьте соответствие форматов в таблицах выше).
