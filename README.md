# SKALDEngine Backend

**SKALD Engine** — высокопроизводительная платформа для интерактивного сторителлинга и ролевых игр с ИИ-персонажами. Построена с использованием **Предметно-ориентированного проектирования (Domain-Driven Design / Vertical Slices)** и оптимизирована для масштабируемости и использования в продакшене.

## Архитектура

Проект использует архитектуру **Vertical Slices** (Вертикальные срезы), где каждая бизнес-область изолирована в собственной директории. Все сервисы используют общую базовую логику в корневой папке `shared/`.

- **services/auth_service/**: Авторизация, JWT и профили пользователей.
- **services/core_service/**: Игровая логика, чаты, ИИ-персонажи, RAG и лорбуки.
- **shared/**: Глобальные базовые классы для репозиториев, сервисов и контроллеров.

---

## Развертывание локально

1. В терминале выполняем команды:

    ```bash
    docker compose up --build -d
    make migrate-auth m="Actualize db structure"
    make migrate-core m="Actualize db structure"
    make upgrade-auth
    make upgrade-core
    ```

2. Для просмотра логов

    ```bash
    docker logs skald_backend -f
    ```

API доступен по адресу <http://localhost:8000>  
Nginx сам раскидает по сервисам

---

## Развертывание в продакшене (Docker)

Проект настроен для развертывания с использованием Docker Compose, где сервисы запускаются в виде двух отдельных контейнеров `auth-service` (порт 8001) и `core-service` (порт 8000), а также баз данных `auth-db` и `core-db` с расширением `pgvector`.

### 1. Настройка окружения
Создайте файл `.env` в корневой директории на основе `.env.example`:
```bash
cp .env.example .env
```
Заполните необходимые переменные (особенно `SECRET_KEY` и `POLZA_API_KEY`).

### 2. Сборка и запуск
```bash
docker compose up -d --build
```
Это действие:
- Соберет единый образ на основе Python 3.11-slim, из которого запускаются оба сервиса.
- Запустит экземпляры PostgreSQL для обоих сервисов на портах 5432 и 5433 соответственно.
- Запустит контейнер `auth-service` (доступен на порту 8001).
- Запустит контейнер `core-service` (доступен на порту 8000).

*Примечание: каждый из контейнеров сервисов также запускает Nginx.*

### 3. Точки доступа API
Для локального доступа при запущенном `core-service` на порту 8000 и `auth-service` на порту 8001:
- **Auth Service (Авторизация)**: `http://localhost:8001/api/v1/auth/...`, `http://localhost:8001/api/v1/users/...`
- **Core Service (Ядро)**: `http://localhost:8000/api/v1/chats/...`, `http://localhost:8000/api/v1/personas/...`, и т.д.
- **Статические файлы (Uploads)**: Доступны по пути `/static/` на любом из сервисов.

---

## Настройка для локальной разработки (без Docker)

Если вам нужно запустить сервисы по отдельности без Docker:

### 1. Настройка базы данных
Убедитесь, что у вас есть две базы данных PostgreSQL (например, `auth_db` на порту 5432 и `core_db` на порту 5433). Для их работы потребуется расширение `pgvector`.

### 2. Окружение
Оба сервиса считывают конфигурацию из корневого файла `.env`.
Убедитесь, что переменные `AUTH_DATABASE_URL` и `CORE_DATABASE_URL` заданы в корневом `.env`.

### 3. Запуск сервисов
**Auth Service (Сервис авторизации):**
```bash
cd services/auth_service
pip install -r requirements.txt
python -m alembic upgrade head
uvicorn app.main:app --reload --port 8001
```

**Core Service (Основной сервис):**
```bash
cd services/core_service
pip install -r requirements.txt
python -m alembic upgrade head
uvicorn app.main:app --reload --port 8002
```
*Примечание: Убедитесь, что при запуске `core-service` вручную вы указываете порт 8002 (как показано в примере), или 8000, в зависимости от ваших настроек фронтенда.*

## Документация
Подробная документация API со всеми эндпоинтами, моделями и ролями безопасности:
👉 [Документация API](api_documentation.md)
