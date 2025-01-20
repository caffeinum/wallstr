from enum import Enum
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Env(str, Enum):
    dev = "dev"
    prod = "prod"
    test = "test"


class JWTSettings(BaseSettings):
    issuer: str = "https://github.com/limanAI/dyvy"
    algorithm: Literal["HS512"] = "HS512"
    access_token_expire_minutes: int = 60
    access_token_renewal_leeway_days: int = 3
    refresh_token_expire_days: int = 7


class Settings(BaseSettings):
    ENV: Env = Env.dev
    DEBUG: bool = False
    DEBUG_SQL: bool = False

    # required
    SECRET_KEY: SecretStr
    DATABASE_URL: SecretStr
    RABBITMQ_URL: SecretStr
    REDIS_URL: SecretStr

    CORS_ALLOW_ORIGINS: list[str] = []

    # JWT
    JWT: JWTSettings = JWTSettings()

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, extra="ignore"
    )


# https://github.com/pydantic/pydantic/issues/3753
settings = Settings.model_validate({})
