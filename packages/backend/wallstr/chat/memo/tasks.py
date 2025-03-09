import asyncio
from pathlib import Path
from uuid import UUID

import structlog
from dramatiq.middleware import CurrentMessage
from langchain_community.callbacks import get_openai_callback
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel
from ruamel.yaml import YAML

from wallstr.chat.llm import SYSTEM_PROMPT
from wallstr.chat.memo.services import MemoService
from wallstr.chat.models import ChatMessageType
from wallstr.chat.services import ChatService
from wallstr.core.llm import SUPPORTED_LLM_MODELS_TYPES, get_llm
from wallstr.core.rate_limiters import get_rate_limiter
from wallstr.core.utils import tiktok
from wallstr.documents.llm import get_rag
from wallstr.logging import debug
from wallstr.worker import dramatiq

logger = structlog.get_logger()


class MemoPrompt(BaseModel):
    name: str
    prompt: str
    example: str


class MemoGroupTemplate(BaseModel):
    name: str
    prompts: list[MemoPrompt]


class MemoTemplate(BaseModel):
    system_prompt: str
    groups: list[MemoGroupTemplate]


try:
    with open(Path(__file__).parent / "prompts.yaml") as fd:
        data = YAML().load(fd)
        MEMO_TEMPLATE = MemoTemplate.model_validate(data["short_memo_template"])
except:
    logger.error("Failed to load memo template")
    raise


@dramatiq.actor  # type: ignore
async def generate_memo(
    message_id: str, user_prompt: str, model: SUPPORTED_LLM_MODELS_TYPES = "gpt-4o"
) -> None:
    ctx = CurrentMessage.get_current_message()
    if not ctx:
        raise Exception("No ctx message")

    db_session_ = ctx.options["session"]
    session_maker = ctx.options["session_maker"]

    chat_svc = ChatService(db_session_)
    message = await chat_svc.get_chat_message(UUID(message_id))
    if not message:
        raise Exception("Message not found")

    if message.message_type != ChatMessageType.MEMO:
        raise Exception("Message is not a memo")

    # TODO: fallback if there is no documents
    document_ids = await chat_svc.get_chat_document_ids(message.chat_id)
    if not document_ids:
        raise Exception("No documents found")

    memo_svc = MemoService(db_session_)
    memo = await memo_svc.get_memo_by_message_id(message.id)
    if not memo:
        memo = await memo_svc.create_memo(message, user_prompt)

    llm = get_llm(model=model)
    rate_limiter = get_rate_limiter(model)

    async def generate_memo_group(group_index: int, group: MemoGroupTemplate) -> None:
        for index, section in enumerate(group.prompts):
            prompt = section.prompt
            debug(f"Prompt:\n {prompt}")

            rag = await get_rag(document_ids, memo.user_id, prompt, distance=0.6)
            if not rag:
                logger.info(f'No RAG for "{group.name} | {section.name}"')
                continue

            messages = [
                SystemMessage(SYSTEM_PROMPT),
                *rag,
                HumanMessage(prompt),
            ]
            async with tiktok(
                f'Generate memo section: "{group.name} | {section.name}"'
            ):
                await rate_limiter.acquire(llm, messages)
                response = await llm.ainvoke(messages)

                if not isinstance(response.content, str):
                    logger.error(f"Invalid response content: {response.content}")
                    return

                async with session_maker() as db_session:
                    chat_svc = MemoService(db_session)
                    await chat_svc.create_memo_section(
                        memo=memo,
                        group=f"{group_index + 1} {group.name}",
                        aspect=section.name,
                        prompt=section.prompt,
                        content=response.content,
                        index=index,
                    )

    with get_openai_callback() as cb:
        async with asyncio.TaskGroup() as tg:
            for task in [
                generate_memo_group(i, group)
                for i, group in enumerate(MEMO_TEMPLATE.groups)
            ]:
                tg.create_task(task)

    logger.info(f"OpenAI tokens used: {cb.total_tokens:_}, cost: {cb.total_cost:.3f}$")
