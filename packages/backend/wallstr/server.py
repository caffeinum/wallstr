import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import TypedDict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from weaviate import WeaviateAsyncClient

from wallstr.auth.api import router as auth_router
from wallstr.chat.api import router as chat_router
from wallstr.chat.dev_api import router as dev_router
from wallstr.conf import config, settings
from wallstr.core.schemas import ConfigResponse
from wallstr.db import AsyncSessionMaker, create_async_engine, create_session_maker
from wallstr.documents.api import router as documents_router
from wallstr.documents.weaviate import get_weaviate_client
from wallstr.logging import configure_logging
from wallstr.openapi import (
    configure_openapi,
    generate_unique_id_function,
)
from wallstr.sse.api import router as sse_router

configure_logging()
logger = logging.getLogger(__name__)


class AppState(TypedDict):
    redis: Redis
    session_maker: AsyncSessionMaker
    wvc: WeaviateAsyncClient


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[AppState, None]:
    engine = create_async_engine(settings.DATABASE_URL, "wallstr")
    session_maker = create_session_maker(engine)

    redis = Redis.from_url(settings.REDIS_URL.get_secret_value())
    wvc = get_weaviate_client(with_openai=True)
    await wvc.connect()
    try:
        yield {
            "redis": redis,
            "session_maker": session_maker,
            "wvc": wvc,
        }
    finally:
        try:
            await redis.aclose()
        except Exception as e:
            logger.exception(e)
        try:
            await engine.dispose()
        except Exception as e:
            logger.exception(e)
        try:
            await wvc.close()
        except Exception as e:
            logger.exception(e)


app = FastAPI(
    version=settings.VERSION,
    lifespan=lifespan,
    generate_unique_id_function=generate_unique_id_function(),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(dev_router)
app.include_router(documents_router)
app.include_router(sse_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": f"wallstr.chat v{settings.VERSION}"}


@app.get("/config", response_model=ConfigResponse)
async def get_config() -> ConfigResponse:
    return ConfigResponse(
        version=settings.VERSION,
        auth={
            "allow_signup": config.AUTH_ALLOW_SIGNUP,
            "providers": config.AUTH_PROVIDERS,
        },
    )


configure_openapi(app)
