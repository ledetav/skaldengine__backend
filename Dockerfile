# ── DEPRECATED: root-level Dockerfile ────────────────────────────────────────
# Этот файл больше не используется напрямую.
# Каждый сервис имеет свой Dockerfile:
#
#   gateway/Dockerfile            — API Gateway (порт 5000)
#   services/auth_service/Dockerfile  — Auth Service (порт 8001)
#   services/core_service/Dockerfile  — Core Service (порт 8000)
#
# Для запуска используй:
#   docker compose up --build
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim
RUN echo "Use 'docker compose up --build' instead of building this image directly." && exit 1
