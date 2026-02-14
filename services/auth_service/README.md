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


## API Эндпоинты

Документация Swagger UI доступна по адресу: `http://localhost:8001/docs`

### Auth (`/api/v1/auth`)

POST `/login` — Вход в систему (OAuth2 Password Flow). Возвращает `access_token`.

POST `/register` — Регистрация нового пользователя.

### Users (`/api/v1/users`)

GET `/me` — Получение информации о текущем пользователе (требует `Header Authorization: Bearer <token>`).