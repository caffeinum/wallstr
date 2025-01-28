from enum import Enum
from typing import Literal, cast

import tomllib
from pydantic import HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_version() -> str:
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)
        return cast(str, data["tool"]["poetry"]["version"])


class Env(str, Enum):
    dev = "dev"
    prod = "prod"
    test = "test"


class JWTSettings(BaseSettings):
    issuer: str = "https://github.com/limanAI/wallstr"
    algorithm: Literal["HS512"] = "HS512"
    access_token_expire_minutes: int = 60
    access_token_renewal_leeway_days: int = 3
    refresh_token_expire_days: int = 7


class Settings(BaseSettings):
    VERSION: str = get_version()
    ENV: Env = Env.dev
    DEBUG: bool = False
    DEBUG_SQL: bool = False

    # required
    SECRET_KEY: SecretStr
    DATABASE_URL: SecretStr
    RABBITMQ_URL: SecretStr
    REDIS_URL: SecretStr
    STORAGE_URL: HttpUrl
    STORAGE_BUCKET: str

    CORS_ALLOW_ORIGINS: list[str] = []

    # JWT
    JWT: JWTSettings = JWTSettings()

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, extra="ignore"
    )


# https://github.com/pydantic/pydantic/issues/3753
settings = Settings.model_validate({})
