from uuid import UUID

from dramatiq.middleware import CurrentMessage
from langchain_openai import OpenAI

from wallstr.chat.services import ChatService
from wallstr.conf import settings
from wallstr.worker import dramatiq


@dramatiq.actor  # type: ignore
async def get_chat_message(message_id: str) -> None:
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
    async for chunk in llm.astream(message.content):
        output = chunk
        await redis.publish(f"{message.user_id}:{message.chat_id}:{message.id}", output)
