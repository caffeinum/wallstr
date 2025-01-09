import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import TypedDict

from fastapi import FastAPI
from redis.asyncio import Redis

from dyvy import worker
from dyvy.conf import settings
from dyvy.db import AsyncSessionMaker, create_async_engine, create_session_maker

logger = logging.getLogger(__name__)


class AppState(TypedDict):
    redis: Redis
    session_maker: AsyncSessionMaker


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[AppState, None]:
    engine = create_async_engine(settings.DATABASE_URL, "dyvy")
    session_maker = create_session_maker(engine)

    redis = Redis.from_url(settings.REDIS_URL.get_secret_value())
    try:
        yield {
            "redis": redis,
            "session_maker": session_maker,
        }
    finally:
        try:
            await redis.close()
        except Exception as e:
            logger.exception(e)


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root(a: int, b: int) -> dict[str, str]:
    worker.add.send(a, b)
    return {"message": f"Job triggered with {a} and {b}"}
