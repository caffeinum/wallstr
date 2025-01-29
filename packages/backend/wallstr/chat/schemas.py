from uuid import UUID

from pydantic import BaseModel, ConfigDict

from wallstr.chat.models import ChatMessageRole
from wallstr.core.schemas import Paginated


class MessageRequest(BaseModel):
    message: str | None
    has_attachments: bool = False


class ChatMessage(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: ChatMessageRole
    content: str


class Chat(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    title: str | None
    messages: Paginated[ChatMessage]
