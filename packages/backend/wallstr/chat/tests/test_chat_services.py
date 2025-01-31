from uuid import uuid4

import pytest
from sqlalchemy import sql
from sqlalchemy.ext.asyncio import AsyncSession

from wallstr.auth.models import UserModel
from wallstr.chat.models import (
    ChatMessageModel,
    ChatModel,
)
from wallstr.chat.schemas import DocumentPayload
from wallstr.chat.services import ChatService
from wallstr.documents.models import DocumentType


@pytest.fixture
def chat_svc(db_session: AsyncSession) -> ChatService:
    return ChatService(db_session)


@pytest.mark.asyncio
async def test_create_chat(chat_svc: ChatService, alice: UserModel) -> None:
    user_message = "Hello, wallstr.chat!"

    chat, _ = await chat_svc.create_chat(user_id=alice.id, user_message=user_message)

    assert chat.user_id == alice.id


@pytest.mark.asyncio
async def test_create_chat_with_documents(
    chat_svc: ChatService, alice: UserModel
) -> None:
    documents = [
        DocumentPayload(filename="report.pdf", doc_type=DocumentType.PDF),
        DocumentPayload(filename="summary.xlsx", doc_type=DocumentType.XLSX),
    ]
    chat, _ = await chat_svc.create_chat(
        user_id=alice.id, user_message=None, documents=documents
    )

    assert chat.user_id == alice.id


@pytest.mark.asyncio
async def test_get_chat(chat_svc: ChatService, chat: ChatModel) -> None:
    result = await chat_svc.get_chat(chat_id=chat.id, user_id=chat.user_id)

    assert result is not None
    assert result.id == chat.id
    assert result.user_id == chat.user_id


@pytest.mark.asyncio
async def test_get_chat_not_found(chat_svc: ChatService, alice: UserModel) -> None:
    non_existent_id = uuid4()
    result = await chat_svc.get_chat(chat_id=non_existent_id, user_id=alice.id)

    assert result is None


@pytest.mark.asyncio
async def test_get_chat_messages(
    chat_svc: ChatService, chat_with_messages: ChatModel
) -> None:
    messages, cursor = await chat_svc.get_chat_messages(
        chat_id=chat_with_messages.id, offset=0, limit=5
    )

    assert len(messages) == 5
    assert cursor == 5


@pytest.mark.asyncio
async def test_get_chat_messages_with_offset(
    chat_svc: ChatService, chat_with_messages: ChatModel
) -> None:
    messages, cursor = await chat_svc.get_chat_messages(
        chat_id=chat_with_messages.id, offset=4, limit=5
    )

    assert len(messages) == 5
    assert cursor == 9


@pytest.mark.asyncio
async def test_get_chat_messages_last_page(
    chat_svc: ChatService, chat_with_messages: ChatModel
) -> None:
    messages, cursor = await chat_svc.get_chat_messages(
        chat_id=chat_with_messages.id, offset=8, limit=5
    )

    assert len(messages) == 2
    assert cursor is None


@pytest.mark.asyncio
async def test_get_chat_messages_empty_chat(
    chat_svc: ChatService, chat: ChatModel
) -> None:
    # First delete the existing message
    async with chat_svc.db.begin():
        await chat_svc.db.execute(
            sql.delete(ChatMessageModel).filter_by(chat_id=chat.id)
        )

    messages, cursor = await chat_svc.get_chat_messages(
        chat_id=chat.id, offset=0, limit=5
    )

    assert len(messages) == 0
    assert cursor is None
