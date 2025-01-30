from uuid import UUID

from pydantic import BaseModel, ConfigDict

from wallstr.chat.models import ChatMessageRole
from wallstr.core.schemas import Paginated
from wallstr.documents.models import DocumentType
from wallstr.documents.schemas import PendingDocument


class DocumentPayload(BaseModel):
    filename: str
    doc_type: DocumentType


class MessageRequest(BaseModel):
    message: str | None
    documents: list[DocumentPayload]


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


class CreateChatResponse(BaseModel):
    chat: Chat
    pending_documents: list[PendingDocument]
