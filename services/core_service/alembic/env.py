"""Конфигурация окружения миграций Alembic для основного игрового сервиса (Core Service).

Настраивает асинхронное подключение к PostgreSQL через SQLAlchemy, регистрирует
все модели предметных областей и задает изолированную таблицу версий alembic_version_core.
"""
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from app.core.config import settings
from app.db.base import Base
from app.domains.character.models import *
from app.domains.lorebook.models import *
from app.domains.persona.models import *
from app.domains.scenario.models import *
from app.domains.chat.models import *
from app.domains.chat.message_models import * 

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Запуск миграций Core Service в офлайн-режиме (без активного подключения к БД)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    """Применяет миграции Core Service с фиксацией версий в таблице alembic_version_core.

    Args:
        connection: Активное синхронное подключение к базе данных.
    """
    context.configure(connection=connection, target_metadata=target_metadata, version_table="alembic_version_core")
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    """Запуск миграций Core Service в онлайн-режиме через асинхронный движок SQLAlchemy."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())