# Makefile
.PHONY: up down restart logs logs-auth logs-core logs-gateway migrate-auth migrate-core upgrade-auth upgrade-core test

up:
	docker compose up -d --build

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f

logs-auth:
	docker compose logs -f auth

logs-core:
	docker compose logs -f core

logs-gateway:
	docker compose logs -f gateway

# Сделать миграцию для Auth (использование: make migrate-auth m="add_user_fields")
migrate-auth:
	docker compose exec auth python -m alembic revision --autogenerate -m '$(m)'

# Сделать миграцию для Core (использование: make migrate-core m="update_chat")
migrate-core:
	docker compose exec core python -m alembic revision --autogenerate -m '$(m)'

upgrade-auth:
	docker compose exec auth python -m alembic upgrade head

upgrade-core:
	docker compose exec core python -m alembic upgrade head

test:
	pytest
