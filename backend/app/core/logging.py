"""Logging setup.

JSON-formatted en producción para parsear fácil desde el VPS. En dev
quedan plain text legibles. La elección la decide el LOG_LEVEL +
detección de tty.
"""
import logging
import sys

from pythonjsonlogger.jsonlogger import JsonFormatter

from app.core.config import get_settings


def configure_logging() -> None:
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    if sys.stdout.isatty():
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s · %(message)s"
            )
        )
    else:
        handler.setFormatter(
            JsonFormatter(
                "%(asctime)s %(levelname)s %(name)s %(message)s",
                rename_fields={"asctime": "ts", "levelname": "level"},
            )
        )
    root.addHandler(handler)
    root.setLevel(level)

    # Calmamos algunos loggers verbosos.
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
