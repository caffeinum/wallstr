import itertools
import math
from collections.abc import Sequence
from typing import Literal

import structlog
import tiktoken
from langchain_core.messages import BaseMessage
from langchain_ollama import ChatOllama
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from PIL.Image import Image

from wallstr.conf import settings

logger = structlog.get_logger()

SUPPORTED_LLM_MODELS_TYPES = Literal["llama3.2", "gpt-4o", "gpt-4o-mini", "llava"]
SUPPORTED_LLM_MODELS_WITH_VISION = ["gpt-4o-mini", "llava"]
SUPPORTED_LLM_MODELS_WITH_VISION_TYPES = Literal["gpt-4o-mini", "llava"]

LLMModel = ChatOllama | ChatOpenAI | AzureChatOpenAI


def get_llm(
    model: SUPPORTED_LLM_MODELS_TYPES | None = None,
) -> LLMModel:
    if model is not None:
        match model:
            case "gpt-4o-mini":
                if settings.MODELS.GPT_4O_MINI is None:
                    raise Exception("Model gpt-4o-mini is not supported in settings")
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
                    f"Not supported provider {settings.MODELS.GPT_4O_MINI.PROVIDER} for gpt-4o-mini"
                )
            case "gpt-4o":
                if settings.MODELS.GPT_4O is None:
                    raise Exception("Model gpt-4o is not supported in settings")
                if settings.MODELS.GPT_4O.PROVIDER == "OPENAI":
                    return ChatOpenAI(
                        api_key=settings.MODELS.GPT_4O.OPENAI_API_KEY
                        or settings.OPENAI_API_KEY,
                        model=settings.MODELS.GPT_4O.NAME,
                    )
                elif settings.MODELS.GPT_4O.PROVIDER == "AZURE":
                    return AzureChatOpenAI(
                        api_key=settings.MODELS.GPT_4O.AZURE_API_KEY,
                        api_version=settings.MODELS.GPT_4O.AZURE_API_VERSION,
                        azure_endpoint=settings.MODELS.GPT_4O.AZURE_API_URL,
                        model=settings.MODELS.GPT_4O.NAME,
                    )
                raise Exception(
                    f"Not supported provider {settings.MODELS.GPT_4O.PROVIDER} for GPT-4o-mini"
                )
            case "llava" | "llama3.2":
                return ChatOllama(
                    model=model, base_url=settings.OLLAMA_URL.get_secret_value()
                )
            case _:
                raise ValueError(f"Unsupported model: {model}")

    if settings.OLLAMA_URL.get_secret_value() is not None:
        return ChatOllama(
            model="llama3.2", base_url=settings.OLLAMA_URL.get_secret_value()
        )

    return ChatOpenAI(api_key=settings.OPENAI_API_KEY, model="gpt-4o-2024-08-06")


def get_llm_with_vision(
    model: SUPPORTED_LLM_MODELS_WITH_VISION_TYPES = "gpt-4o-mini",
) -> ChatOpenAI | AzureChatOpenAI:
    llm = get_llm(model)
    if not isinstance(llm, ChatOpenAI) and not isinstance(llm, AzureChatOpenAI):
        raise ValueError(f"Only ChatOpenAI model supports vision, got {llm}")
    return llm


def estimate_input_tokens(
    llm: LLMModel,
    input_: str | Sequence[BaseMessage],
    *,
    image: Image | None = None,
    image_mode: Literal["low", "high", "auto"] = "auto",
) -> int:
    enc = None
    if isinstance(llm, (ChatOpenAI, AzureChatOpenAI)):
        if llm.model_name is None:
            logger.warning(
                f"Model name is not set for {llm}, cannot estimate input tokens"
            )
            return 0

        enc = tiktoken.encoding_for_model(llm.model_name)

    if enc is None:
        logger.warning(f"Cannot get tokens encoding for {llm}")
        return 0

    input_enc = []
    if isinstance(input_, str):
        input_enc = enc.encode(input_)
    if isinstance(input_, list):
        content = _merge_langchain_messages(input_)
        input_enc = list(
            itertools.chain(*[enc.encode(raw_message) for raw_message in content])
        )
    input_tokens = len(input_enc)

    if image is not None:
        input_tokens += estimate_input_tokens_for_image(llm, image, image_mode)
    return input_tokens


def estimate_input_tokens_for_image(
    llm: LLMModel, image: Image, image_mode: Literal["low", "high", "auto"] = "auto"
) -> int:
    """
    Getting tokens for models with vision
    Only OpenAI models supported:
    https://platform.openai.com/docs/guides/vision#low-or-high-fidelity-image-understanding
    """
    logger.trace(
        f"Calculate input tokens for {image.size[0]}x{image.size[1]} image, mode: {image_mode}"
    )
    if not isinstance(llm, (ChatOpenAI, AzureChatOpenAI)):
        logger.warning(f"Token estimation for image is not implemented for {llm}")
        return 0

    if llm.model_name not in SUPPORTED_LLM_MODELS_WITH_VISION:
        logger.warning("Model does not support vision")
        return 0
    if image_mode == "low":
        return 85

    if image_mode == "auto" and max(image.size) <= 512:
        return 85

    MAX_SIZE = 2048
    MIN_SIZE = 768

    max_side: float = min(MAX_SIZE, max(image.size))
    scale = max_side / max(image.size)
    min_side = min(image.size) * scale

    scale = MIN_SIZE / min_side
    min_side = MIN_SIZE
    max_side = scale * max_side

    square = max_side * min_side
    tiles = math.ceil(square / 512**2)
    return 170 * tiles + 85


def _merge_langchain_messages(
    input_: Sequence[BaseMessage],
) -> list[str]:
    """
    Returns list with raw text from LangChain messages
    """
    output = []
    for message in input_:
        content = message.content
        if isinstance(content, str):
            output.append(content)
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, str):
                    output.append(item)
                elif isinstance(item, dict) and item["type"] == "text":
                    output.append(item["text"])
        else:
            logger.warning(f"Unsupported message type {message}")
    return output
