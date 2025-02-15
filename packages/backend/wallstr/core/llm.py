from typing import Literal

from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from wallstr.conf import settings

SUPPORTED_LLM_MODELS = Literal["llama3.2", "gpt-4o", "gpt-4o-mini", "llava"]
SUPPORTED_LLM_MODELS_WITH_VISION = Literal["gpt-4o-mini", "llava"]

LLMModel = ChatOllama | ChatOpenAI


def get_llm(
    model: SUPPORTED_LLM_MODELS | None = None,
) -> LLMModel:
    if model is not None:
        match model:
            case "gpt-4o-mini":
                return ChatOpenAI(api_key=settings.OPENAI_API_KEY, model="gpt-4o-mini")
            case "gpt-4o":
                return ChatOpenAI(
                    api_key=settings.OPENAI_API_KEY, model="gpt-4o-2024-08-06"
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
