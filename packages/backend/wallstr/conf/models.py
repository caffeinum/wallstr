from typing import Literal
from urllib.parse import parse_qs, urlparse

from pydantic import SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ModelConfig(BaseSettings):
    # Tokens per minute
    TPM: int

    # Tokens per day
    TPD: int

    # Requests per minute
    RPM: int


class OpenAIModelConfig(ModelConfig):
    NAME: str
    PROVIDER: Literal["OPENAI", "AZURE"] = "OPENAI"
    AZURE_API_URL: str | None = None
    AZURE_API_KEY: SecretStr | None = None
    OPENAI_API_KEY: SecretStr | None = None

    @computed_field  # type: ignore[misc]
    @property
    def AZURE_API_VERSION(self) -> str:
        if not self.AZURE_API_URL:
            raise ValueError(f"Missing Azure API URL for model {self.NAME}")
        parsed_url = urlparse(self.AZURE_API_URL)

        if not parsed_url.query:
            raise ValueError(
                f"Missing query parameters in Azure API URL {self.AZURE_API_URL}"
            )
        api_version = parse_qs(str(parsed_url.query)).get("api-version", [])[0]
        if not api_version:
            raise ValueError(
                f"Missing api-version in Azure API URL {self.AZURE_API_URL}"
            )
        return str(api_version)


class Gpt4oConfig(OpenAIModelConfig):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
    )
    NAME: str = "gpt-4o"
    TPM: int = 450_000
    TPD: int = 1_350_000
    RPM: int = 5_000


class Gpt4oMiniConfig(OpenAIModelConfig):
    NAME: str = "gpt-4o-mini"
    TPM: int = 2_000_000
    TPD: int = 20_000_000
    RPM: int = 5_000


class ModelsConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="MODELS",
        case_sensitive=True,
        extra="ignore",
    )
    GPT_4O: Gpt4oConfig = Gpt4oConfig()
    GPT_4O_MINI: Gpt4oMiniConfig = Gpt4oMiniConfig()
