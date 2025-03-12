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


TGpt4o = Literal["gpt-4o"]
TGpt4oMini = Literal["gpt-4o-mini"]
TLlama3_70b = Literal["llama3-70b"]

SUPPORTED_LLM_MODELS_TYPES = TGpt4o | TGpt4oMini | TLlama3_70b


class OpenAIModelConfig(ModelConfig):
    NAME: TGpt4o | TGpt4oMini
    PROVIDER: Literal["OPENAI", "AZURE"]
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
    """
    https://platform.openai.com/docs/models/gpt-4o
    """

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
    )
    NAME: TGpt4o | TGpt4oMini = "gpt-4o"

    TPM: int = 450_000
    TPD: int = 1_350_000
    RPM: int = 5_000

    context_window: int = 128_000


class Gpt4oMiniConfig(OpenAIModelConfig):
    """
    https://platform.openai.com/docs/models/gpt-4o-mini
    """

    NAME: TGpt4o | TGpt4oMini = "gpt-4o-mini"

    TPM: int = 2_000_000
    TPD: int = 20_000_000
    RPM: int = 5_000

    context_window: int = 128_000


class Llama3_70bConfig(ModelConfig):
    NAME: TLlama3_70b = "llama3-70b"
    PROVIDER: Literal["REPLICATE"]
    REPLICATE_API_KEY: SecretStr | None = None

    # Not supported
    TPM: int = 0
    TPD: int = 0
    RPM: int = 0

    context_window: int = 8_000


class ModelsConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="MODELS",
        case_sensitive=True,
        extra="ignore",
    )
    GPT_4O: Gpt4oConfig | None = None
    GPT_4O_MINI: Gpt4oMiniConfig | None = None
    LLAMA3_70B: Llama3_70bConfig | None = None

    @computed_field  # type: ignore[misc]
    @property
    def get_enabled_models(self) -> list[SUPPORTED_LLM_MODELS_TYPES]:
        enabled_models = []
        for model in self.__dict__.values():
            if model and model.NAME:
                enabled_models.append(model.NAME)
        return enabled_models
