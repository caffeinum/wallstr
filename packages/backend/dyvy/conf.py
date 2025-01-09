from enum import Enum

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Env(str, Enum):
    dev = "dev"
    prod = "prod"


class Settings(BaseSettings):
    ENV: Env = Env.dev
    DEBUG: bool = False
    DEBUG_SQL: bool = False

    # required
    DATABASE_URL: SecretStr
    RABBITMQ_URL: SecretStr
    REDIS_URL: SecretStr

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, extra="ignore"
    )


# https://github.com/pydantic/pydantic/issues/3753
settings = Settings.model_validate({})
