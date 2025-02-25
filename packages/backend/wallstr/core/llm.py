from typing import Literal

from langchain_ollama import ChatOllama
from langchain_openai import AzureChatOpenAI, ChatOpenAI

from wallstr.conf import settings

SUPPORTED_LLM_MODELS = Literal["llama3.2", "gpt-4o", "gpt-4o-mini", "llava"]
SUPPORTED_LLM_MODELS_WITH_VISION = Literal["gpt-4o-mini", "llava"]

LLMModel = ChatOllama | ChatOpenAI | AzureChatOpenAI


def get_llm(
    model: SUPPORTED_LLM_MODELS | None = None,
) -> LLMModel:
    if model is not None:
        match model:
            case "gpt-4o-mini":
                if settings.MODELS.GPT_4O_MINI.PROVIDER == "OPENAI":
                    return ChatOpenAI(
                        api_key=settings.MODELS.GPT_4O_MINI.OPENAI_API_KEY
                        or settings.OPENAI_API_KEY,
                        model=settings.MODELS.GPT_4O_MINI.NAME,
                    )
                elif settings.MODELS.GPT_4O_MINI.PROVIDER == "AZURE":
                    return AzureChatOpenAI(
                        api_key=settings.MODELS.GPT_4O_MINI.AZURE_API_KEY,
                        api_version=settings.MODELS.GPT_4O_MINI.AZURE_API_VERSION,
                        azure_endpoint=settings.MODELS.GPT_4O_MINI.AZURE_API_URL,
                        model=settings.MODELS.GPT_4O_MINI.NAME,
                    )
                raise Exception(
                    f"Not supported provider {settings.MODELS.GPT_4O_MINI.PROVIDER} for GPT-4o-mini"
                )
            case "gpt-4o":
                if settings.MODELS.GPT_4O.PROVIDER == "OPENAI":
                    return ChatOpenAI(
                        api_key=settings.MODELS.GPT_4O.OPENAI_API_KEY
                        or settings.OPENAI_API_KEY,
                        model=settings.MODELS.GPT_4O.NAME,
                    )
                elif settings.MODELS.GPT_4O.PROVIDER == "AZURE":
                    return AzureChatOpenAI(
                        api_key=settings.MODELS.GPT_4O.AZURE_API_KEY,
                        api_version=settings.MODELS.GPT_4O_MINI.AZURE_API_VERSION,
                        azure_endpoint=settings.MODELS.GPT_4O.AZURE_API_URL,
                        model=settings.MODELS.GPT_4O.NAME,
                    )
                raise Exception(
                    f"Not supported provider {settings.MODELS.GPT_4O_MINI.PROVIDER} for GPT-4o-mini"
                )
            case "llava" | "llama3.2":
                return ChatOllama(
                    model=model, base_url=settings.OLLAMA_URL.get_secret_value()
                )
            case _:
                raise ValueError(f"Invalid model {model}")

    if settings.OLLAMA_URL.get_secret_value() is not None:
        return ChatOllama(
            model="llama3.2", base_url=settings.OLLAMA_URL.get_secret_value()
        )

    return ChatOpenAI(api_key=settings.OPENAI_API_KEY, model="gpt-4o-2024-08-06")


def get_llm_with_vision(
    model: SUPPORTED_LLM_MODELS_WITH_VISION = "gpt-4o-mini",
) -> ChatOpenAI:
    llm = get_llm(model)
    if not isinstance(llm, ChatOpenAI):
        raise ValueError(f"Only ChatOpenAI model supports vision, got {llm}")
    return llm
