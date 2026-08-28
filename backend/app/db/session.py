from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

settings = get_settings()


@lru_cache
def get_session_factory() -> sessionmaker:
    engine = create_engine(settings.sqlalchemy_database_url, pool_pre_ping=True)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@lru_cache
def get_async_session_factory() -> async_sessionmaker[AsyncSession]:
    async_engine = create_async_engine(settings.sqlalchemy_async_database_url, pool_pre_ping=True)
    return async_sessionmaker(bind=async_engine, autoflush=False, expire_on_commit=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with get_async_session_factory()() as session:
        yield session
