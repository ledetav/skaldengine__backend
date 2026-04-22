# Makefile
.PHONY: migrate-auth migrate-core upgrade-auth upgrade-core

# Сделать миграцию для Auth (использование: make migrate-auth m="add_user_fields")
migrate-auth:
	docker exec -u root -it skald_backend bash -c "cd services/auth_service && alembic revision --autogenerate -m '$(m)'"

# Сделать миграцию для Core (использование: make migrate-core m="update_chat")
migrate-core:
	docker exec -u root -it skald_backend bash -c "cd services/core_service && alembic revision --autogenerate -m '$(m)'"

upgrade-auth:
	docker exec -u root -it skald_backend bash -c "cd services/auth_service && alembic upgrade head"

upgrade-core:
	docker exec -u root -it skald_backend bash -c "cd services/core_service && alembic upgrade head"
