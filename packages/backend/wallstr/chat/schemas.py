from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, computed_field

from wallstr.chat.memo.schemas import Memo
from wallstr.chat.models import ChatMessageRole, ChatMessageType
from wallstr.core.schemas import SSE, Paginated
from wallstr.documents.models import DocumentType
from wallstr.documents.schemas import Document, PendingDocument


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
    message_type: ChatMessageType
    documents: list[Document]
    pending_documents: list[PendingDocument] = []
    memo: Memo | None = None

    created_at: datetime


class Chat(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    title: str | None
    messages: Paginated[ChatMessage]


class ChatMessageSSE(SSE):
    id: UUID
    content: str

    @computed_field
    def type(self) -> str:
        return "message"


class ChatMessageStartSSE(SSE):
    id: UUID

    @computed_field
    def type(self) -> str:
        return "message_start"


class ChatMessageEndSSE(SSE):
    id: UUID
    new_id: UUID
    created_at: datetime
    content: str

    @computed_field
    def type(self) -> str:
        return "message_end"
