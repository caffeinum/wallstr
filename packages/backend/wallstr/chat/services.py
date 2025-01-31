from uuid import UUID

from sqlalchemy import select, sql

from wallstr.chat.models import (
    ChatMessageModel,
    ChatMessageRole,
    ChatModel,
)
from wallstr.chat.schemas import DocumentPayload
from wallstr.documents.models import DocumentModel, DocumentStatus
from wallstr.services import BaseService


class ChatService(BaseService):
    async def get_chat(self, chat_id: UUID, user_id: UUID) -> ChatModel | None:
        async with self.tx():
            result = await self.db.execute(
                select(ChatModel).filter_by(
                    id=chat_id, user_id=user_id, deleted_at=None
                )
            )
        return result.scalar_one_or_none()

    async def get_chat_by_slug(self, chat_slug: str, user_id: UUID) -> ChatModel | None:
        async with self.tx():
            result = await self.db.execute(
                select(ChatModel).filter_by(
                    slug=chat_slug, user_id=user_id, deleted_at=None
                )
            )
        return result.scalar_one_or_none()

    async def get_chat_message(self, message_id: UUID) -> ChatMessageModel | None:
        async with self.tx():
            result = await self.db.execute(
                sql.select(ChatMessageModel).filter_by(id=message_id)
            )

            message = result.scalar_one_or_none()
        return message

    async def get_chat_messages(
        self, chat_id: UUID, offset: int = 0, limit: int = 10
    ) -> tuple[list[ChatMessageModel], int | None]:
        async with self.tx():
            result = await self.db.execute(
                sql.select(ChatMessageModel)
                .filter_by(chat_id=chat_id)
                .order_by(ChatMessageModel.created_at.desc())
                .offset(offset)
                .limit(limit + 1)
            )

            messages = result.scalars().all()
            has_more = len(messages) > limit
            new_cursor = offset + limit if has_more else None
        return list(messages[:limit]), new_cursor

    async def get_user_chats(
        self, user_id: UUID, offset: int = 0, limit: int = 10
    ) -> tuple[list[ChatModel], int | None]:
        async with self.tx():
            result = await self.db.execute(
                select(ChatModel)
                .filter_by(user_id=user_id, deleted_at=None)
                .order_by(ChatModel.created_at.desc())
                .offset(offset)
                .limit(limit + 1)
            )

            chats = result.scalars().all()
            has_more = len(chats) > limit
            new_cursor = offset + limit if has_more else None
        return list(chats[:limit]), new_cursor

    async def create_chat(
        self,
        user_id: UUID,
        user_message: str | None,
        documents: list[DocumentPayload] | None = None,
    ) -> tuple[ChatModel, ChatMessageModel]:
        documents = documents or []
        async with self.tx():
            chat_message = ChatMessageModel(
                user_id=user_id,
                role=ChatMessageRole.USER,
                content=user_message,
                documents=[
                    DocumentModel(
                        **document.model_dump(),
                        user_id=user_id,
                        storage_path=f"{user_id}/{document.filename}",
                        status=DocumentStatus.UPLOADING,
                    )
                    for document in documents
                ],
            )
            chat = ChatModel(
                user_id=user_id,
                messages=[chat_message],
            )
            self.db.add(chat)
        return chat, chat_message

    async def create_chat_message(
        self,
        chat_id: UUID,
        message: str | None,
        documents: list[DocumentPayload] | None = None,
        role: ChatMessageRole = ChatMessageRole.USER,
    ) -> ChatMessageModel:
        documents = documents or []
        async with self.tx():
            result = await self.db.execute(
                select(ChatModel).filter_by(id=chat_id, deleted_at=None)
            )
            chat = result.scalar_one_or_none()
            if not chat:
                raise ValueError("Chat not found")

            chat_message = ChatMessageModel(
                chat_id=chat_id,
                user_id=chat.user_id,
                role=role,
                content=message,
                documents=[
                    DocumentModel(
                        **document.model_dump(),
                        user_id=chat.user_id,
                        storage_path=f"{chat.user_id}/{document.filename}",
                        status=DocumentStatus.UPLOADING,
                    )
                    for document in documents
                ],
            )
            self.db.add(chat_message)
        return chat_message
