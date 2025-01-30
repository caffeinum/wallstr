from uuid import UUID

from dramatiq.middleware import CurrentMessage

from wallstr.chat.services import ChatService
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
        raise Exception("Not found")
    print(message)
