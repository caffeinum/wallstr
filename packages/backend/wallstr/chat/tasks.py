from uuid import UUID

from dramatiq.middleware import CurrentMessage
from langchain_openai import OpenAI

from wallstr.chat.models import ChatMessageRole
from wallstr.chat.services import ChatService
from wallstr.conf import settings
from wallstr.worker import dramatiq


@dramatiq.actor  # type: ignore
async def process_chat_message(message_id: str) -> None:
    ctx = CurrentMessage.get_current_message()
    if not ctx:
        raise Exception("No ctx message")

    db_session = ctx.options.get("session")
    if not db_session:
        raise Exception("No session")

    chat_svc = ChatService(db_session)
    message = await chat_svc.get_chat_message(UUID(message_id))
    if not message:
        raise Exception("Message not found")

    redis = ctx.options.get("redis")
    if not redis:
        raise Exception("No redis")

    llm = OpenAI(api_key=settings.OPENAI_API_KEY)
    chunks = []
    async for chunk in llm.astream(message.content):
        chunks.append(chunk)
        await redis.publish(f"{message.user_id}:{message.chat_id}:{message.id}", chunk)

    await chat_svc.create_chat_message(
        chat_id=message.chat_id,
        message="".join(chunks),
        role=ChatMessageRole.ASSISTANT,
    )
