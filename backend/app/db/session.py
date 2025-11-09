"""Async session management."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import get_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Return a singleton async engine."""

    global _engine, _session_factory
    if _engine is None:
        settings = get_settings()
        url = make_url(settings.database.url)
        engine_kwargs: dict[str, object] = {
            "echo": settings.database.echo,
        }
        if url.get_backend_name() == "sqlite":
            engine_kwargs["poolclass"] = NullPool
        else:
            engine_kwargs["pool_size"] = settings.database.pool_size
            engine_kwargs["max_overflow"] = settings.database.max_overflow
        _engine = create_async_engine(settings.database.url, **engine_kwargs)
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


@asynccontextmanager
async def async_session() -> AsyncIterator[AsyncSession]:
    """Provide an async session dependency."""

    global _session_factory
    if _session_factory is None:
        get_engine()
    assert _session_factory is not None  # for type checker
    async with _session_factory() as session:
        yield session
