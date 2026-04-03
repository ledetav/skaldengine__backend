# Skald Auth Service

Микросервис, отвечающий за регистрацию, аутентификацию и управление учетными записями пользователей. Работает независимо от игровой логики.

## Технический стек

- Framework: FastAPI
- Database: PostgreSQL (Async via asyncpg)
- ORM: SQLAlchemy 2.0
- Migrations: Alembic
- Auth: JWT (JSON Web Tokens) + BCrypt (Password Hashing)

## Запуск и Настройка

1. Переменные окружения (.env)

Создайте файл `.env` в папке сервиса из `.env.example`:
```
PROJECT_NAME="Skald Auth Service"
API_V1_STR="/api/v1"
SECRET_KEY="your-secret-key-shared-with-core"
DATABASE_URL="postgresql+asyncpg://auth_user:auth_password@localhost:5432/auth_db"
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

**Важно**: `SECRET_KEY` должен совпадать с тем, что используется в Core Service, чтобы тот мог валидировать токены.

2. Установка зависимостей
```
python -m venv venv
source venv/bin/activate  # или venv\Scripts\activate на Windows
pip install -r requirements.txt
```

3. Миграции БД

### Создать миграцию (если изменились модели)
`python -m alembic revision --autogenerate -m "message"`

### Применить миграции
`python -m alembic upgrade head`

4. Запуск сервера

Сервис запускается на порту `8001`.

`uvicorn app.main:app --reload --port 8001`


## Подробная документация API

Все запросы должны иметь заголовок `Content-Type: application/json`. Эндпоинты, помеченные как **[Auth]**, требуют заголовок `Authorization: Bearer <token>`.

### 1. Аутентификация (`/api/v1/auth`)

#### `POST /register`
**Назначение:** Регистрация нового пользователя.
- **Принимает:** `UserCreate` (JSON)
  - `email`: string (валидный email)
  - `username`: string (без пробелов по краям, только латиница, цифры, `-` и `_`)
  - `birth_date`: date (обязательно)
  - `password`: string (мин 8 символов, 1 цифра, 1 заглавная, 1 спецсимвол)
- **Возвращает:** Объект пользователя (без пароля).
- **Пример ввода:**
  ```json
  {
    "email": "user@example.com",
    "username": "Skald_Player",
    "birth_date": "1995-04-03",
    "password": "StrongPassword123!"
  }
  ```



#### `POST /login`
**Назначение:** Получение JWT токена доступа.
- **Принимает:** `form-data` (application/x-www-form-urlencoded)
  - `username`: (email или username пользователя)
  - `password`: пароль
- **Возвращает:** JSON с токеном.
  - `access_token`: JWT строка.
  - `token_type`: "bearer"
- **Пример ответа:**
  ```json
  {
    "access_token": "eyJhbG...",
    "token_type": "bearer"
  }
  ```

### 2. Пользователи (`/api/v1/users`)

#### `GET /me` [Auth]
**Назначение:** Получение полного профиля пользователя.

#### `GET /me/username` [Auth]
**Назначение:** Получить только никнейм.
- **Ответ:** `{"username": "CurrentName"}`

#### `PATCH /me/username` [Auth]
**Назначение:** Изменить никнейм.
- **Тело:** `{"new_username": "NewName"}`

#### `PATCH /me/email` [Auth]
**Назначение:** Изменить почту.
- **Тело:** `{"new_email": "new@example.com"}`

#### `POST /me/password` [Auth]
**Назначение:** Смена пароля.
- **Тело:** `{"old_password": "...", "new_password": "..."}`

#### `DELETE /me` [Auth]
**Назначение:** Удаление аккаунта. Требует статус 204 при успехе.

