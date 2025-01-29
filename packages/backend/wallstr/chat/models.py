import enum
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, WriteOnlyMapped, mapped_column, relationship

from wallstr.core.utils import generate_unique_slug
from wallstr.models.base import RecordModel, string_column


class ChatModel(RecordModel):
    __tablename__ = "chats"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("auth_users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    slug: Mapped[str] = mapped_column(
        String(12), unique=True, default=generate_unique_slug
    )
    title: Mapped[str] = string_column(length=255)
    messages: WriteOnlyMapped[list["ChatMessageModel"]] = relationship(
        back_populates="chat", cascade="all, delete-orphan"
    )


class ChatMessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessageModel(RecordModel):
    __tablename__ = "chat_messages"
    __table_args__ = (
        Index(
            "ix_chat_messages_chat_id_created_at",
            "chat_id",
            "created_at",
            postgresql_using="btree",
        ),
    )

    chat_id: Mapped[UUID] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    role: Mapped[ChatMessageRole] = mapped_column(Enum(ChatMessageRole), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")

    chat: Mapped[ChatModel] = relationship(back_populates="messages")
    documents: Mapped[list["ChatDocumentModel"]] = relationship(
        secondary="chat_documents_x_messages",
        lazy="selectin",
    )


class ChatDocumentType(str, enum.Enum):
    PDF = "pdf"
    DOC = "doc"
    DOCX = "docx"
    XLS = "xls"
    XLSX = "xlsx"


class ChatDocumentModel(RecordModel):
    __tablename__ = "chat_documents"

    user_id: Mapped[UUID] = mapped_column(nullable=False, index=True)

    filename: Mapped[str] = string_column(length=255, nullable=False)
    file_size: Mapped[int] = mapped_column(nullable=False)
    doc_type: Mapped[ChatDocumentType] = mapped_column(
        Enum(ChatDocumentType), nullable=False
    )
    storage_path: Mapped[str] = string_column(length=1024, nullable=False)
    page_count: Mapped[int] = mapped_column(nullable=True)


class ChatDocumentXMessageModel(RecordModel):
    __tablename__ = "chat_documents_x_messages"

    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("chat_documents.id", ondelete="CASCADE"), primary_key=True
    )
    message_id: Mapped[UUID] = mapped_column(
        ForeignKey("chat_messages.id", ondelete="CASCADE"), primary_key=True
    )
