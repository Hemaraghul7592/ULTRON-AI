from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

engine: AsyncEngine | None = None
session_factory: async_sessionmaker[AsyncSession] | None = None


class Base(DeclarativeBase):
    pass


async def init_db() -> None:
    global engine, session_factory

    settings = get_settings()
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DB_ECHO,
        pool_pre_ping=True,
        **({"pool_size": 20, "max_overflow": 10} if settings.is_postgres else {}),
    )
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def close_db() -> None:
    global engine
    if engine:
        await engine.dispose()


def get_session() -> async_sessionmaker[AsyncSession]:
    if session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return session_factory


def get_engine() -> AsyncEngine | None:
    return engine
