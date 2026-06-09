"""SQLAlchemy 2.x async engine + session factory.

Usamos `AsyncSession` para que el endpoint pueda ser `async def` sin
bloquear el event loop en queries lentas. El engine se crea una sola
vez al arrancar y se cierra al cerrar la app (lifespan en main.py).
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Base declarativa única — todos los modelos heredan de acá."""


_settings = get_settings()
_engine: AsyncEngine = create_async_engine(
    _settings.database_url,
    echo=_settings.log_level == "DEBUG",
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)
_SessionFactory = async_sessionmaker(
    _engine, expire_on_commit=False, autoflush=False
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency de FastAPI para inyectar una sesión por request."""
    async with _SessionFactory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        else:
            # Commit explícito en el endpoint si la op no fue read-only.
            # No commiteamos acá automáticamente porque algunos endpoints
            # son puros de lectura y no quieren disparar `BEGIN`.
            pass


async def dispose_engine() -> None:
    await _engine.dispose()
