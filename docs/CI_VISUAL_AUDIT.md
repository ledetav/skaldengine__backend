# Автоматическая проверка бэкенда и кросс-репозиторный UI-аудит

## Назначение

Пайплайн `.github/workflows/backend-verify.yml` автоматически запускается при создании Pull Request в `main` и при каждом пуше в рабочие ветки (`feat/**`, `fix/**`, `refactor/**`).

## Этапы проверки

1. **Статический анализ (`Ruff`):** проверка стиля и импортов в `gateway`, `services` и `shared`.
2. **Автотесты (`Pytest`):** запуск юнит- и интеграционных тестов в изолированном тестовом окружении (SQLite + тестовые секреты).
3. **Кросс-репозиторный триггер (`repository_dispatch`):** после завершения проверки отправляет событие `backend-updated` с именем текущей ветки в репозиторий `ledetav/skaldengine__frontend`. Фронтовой CI подтягивает одноименную ветку бэкенда и запускает сквозной визуальный аудит интерфейса на живом API.

## Необходимые секреты репозитория

- `CROSS_REPO_TOKEN` — Fine-grained Personal Access Token с правом `Contents: Read and write` на репозитории `ledetav/skaldengine__backend` и `ledetav/skaldengine__frontend`.
