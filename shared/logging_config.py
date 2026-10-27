"""Конфигурация структурированного логирования для приложения."""

import logging
import sys


def setup_logging(log_level: str = "INFO"):
    """Настраивает корневой логгер и форматирование логов для консольного вывода.

    Args:
        log_level: Уровень логирования в виде строки (например, "INFO", "DEBUG").
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Настройка логгеров Uvicorn и FastAPI: удаляем их собственные обработчики,
    # чтобы все логи проходили через корневой логгер с нашим форматом.
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        logger = logging.getLogger(logger_name)
        logger.handlers = []
        logger.propagate = True

