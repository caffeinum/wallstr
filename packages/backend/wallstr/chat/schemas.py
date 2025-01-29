from uuid import UUID

from pydantic import BaseModel

from wallstr.chat.models import ChatMessageRole
from wallstr.core.schemas import Paginated


class MessageRequest(BaseModel):
    message: str | None
    has_attachments: bool = False


class ChatMessage(BaseModel):
    id: UUID
    role: ChatMessageRole
    content: str


class Chat(BaseModel):
    id: UUID
    title: str | None
    messages: Paginated[ChatMessage]
