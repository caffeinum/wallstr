from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
from sqlalchemy import sql
from sqlalchemy.ext.asyncio import AsyncSession

from wallstr.auth.models import UserModel
from wallstr.chat.models import ChatMessageModel, ChatMessageRole, ChatModel
from wallstr.chat.services import ChatService


@pytest.fixture
def chat_svc(db_session: AsyncSession) -> ChatService:
    return ChatService(db_session)


@pytest.fixture
async def chat(db_session: AsyncSession, alice: UserModel) -> AsyncGenerator[ChatModel]:
    async with db_session.begin():
        result = await db_session.execute(
            sql.insert(ChatModel).values(user_id=alice.id).returning(ChatModel)
        )
        chat = result.scalar_one()

        await db_session.execute(
            sql.insert(ChatMessageModel).values(
                chat_id=chat.id,
                user_id=alice.id,
                role=ChatMessageRole.USER,
                content="Hello, how are you?",
            )
        )
    yield chat
    async with db_session.begin():
        await db_session.execute(
            sql.delete(ChatMessageModel).filter_by(chat_id=chat.id)
        )
        await db_session.execute(sql.delete(ChatModel).filter_by(id=chat.id))


@pytest.fixture
async def chat_with_messages(
    db_session: AsyncSession, alice: UserModel
) -> AsyncGenerator[ChatModel]:
    async with db_session.begin():
        result = await db_session.execute(
            sql.insert(ChatModel).values(user_id=alice.id).returning(ChatModel)
        )
        chat = result.scalar_one()

        messages = [
            {
                "chat_id": chat.id,
                "user_id": alice.id,
                "role": ChatMessageRole.USER,
                "content": f"User message {i}",
            }
            for i in range(5)
        ] + [
            {
                "chat_id": chat.id,
                "user_id": alice.id,
                "role": ChatMessageRole.ASSISTANT,
                "content": f"Assistant response {i}",
            }
            for i in range(5)
        ]

        for msg in messages:
            await db_session.execute(sql.insert(ChatMessageModel).values(**msg))

    yield chat
    async with db_session.begin():
        await db_session.execute(
            sql.delete(ChatMessageModel).filter_by(chat_id=chat.id)
        )
        await db_session.execute(sql.delete(ChatModel).filter_by(id=chat.id))


@pytest.mark.asyncio
async def test_create_chat(chat_svc: ChatService, alice: UserModel) -> None:
    user_message = "Hello, wallstr.chat!"

    chat = await chat_svc.create_chat(user_id=alice.id, user_message=user_message)

    assert chat.user_id == alice.id


@pytest.mark.asyncio
async def test_create_chat_without_message(
    chat_svc: ChatService, alice: UserModel
) -> None:
    chat = await chat_svc.create_chat(user_id=alice.id, user_message=None)

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
