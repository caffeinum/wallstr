from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from dyvy.conf import settings
from dyvy.db import create_async_engine, create_session_maker
from dyvy.logging import configure_logging
from dyvy.models.base import BaseModel


@pytest_asyncio.fixture(scope="session")
async def session_engine() -> AsyncGenerator[AsyncEngine]:
    engine = create_async_engine(settings.DATABASE_URL, "test")
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def configure(session_engine: AsyncEngine) -> AsyncGenerator[None]:
    async with session_engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
    configure_logging()
    yield
    async with session_engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)


@pytest_asyncio.fixture
async def engine() -> AsyncGenerator[AsyncEngine]:
    engine = create_async_engine(settings.DATABASE_URL, "test")
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(
    engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession]:
    session_maker = create_session_maker(engine)
    async with session_maker() as session:
        yield session
