import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from wallstr.auth.dependencies import Auth
from wallstr.auth.schemas import HTTPUnauthorizedError
from wallstr.chat.schemas import (
    Chat,
    ChatMessage,
    CreateChatResponse,
    MessageRequest,
)
from wallstr.chat.services import ChatService
from wallstr.core.schemas import Paginated
from wallstr.documents.models import DocumentModel
from wallstr.documents.schemas import PendingDocument
from wallstr.documents.services import DocumentService
from wallstr.openapi import generate_unique_id_function

router = APIRouter(
    prefix="/chats",
    tags=["chat"],
    generate_unique_id_function=generate_unique_id_function(2),
    responses={401: {"model": HTTPUnauthorizedError}},
)


@router.post(
    "",
    response_model=CreateChatResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_chat(
    data: MessageRequest,
    auth: Auth,
    chat_svc: Annotated[ChatService, Depends(ChatService.inject_svc)],
    document_svc: Annotated[DocumentService, Depends(DocumentService.inject_svc)],
) -> CreateChatResponse:
    if data.message is None and len(data.documents) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot start chat without message",
        )
    chat, message = await chat_svc.create_chat(
        user_id=auth.user_id,
        user_message=data.message,
        documents=data.documents,
    )

    async def get_pending_document(document: DocumentModel) -> PendingDocument:
        return PendingDocument(
            id=document.id,
            filename=document.filename,
            presigned_url=document_svc.generate_upload_url(auth.user_id, document),
        )

    pending_documents = await asyncio.gather(
        *[get_pending_document(document) for document in message.documents]
    )

    return CreateChatResponse(
        chat=Chat(
            id=chat.id,
            title=chat.title,
            slug=chat.slug,
            messages=Paginated(
                items=[ChatMessage.model_validate(message)],
                cursor=None,
            ),
        ),
        pending_documents=pending_documents,
    )


@router.get("/{slug}")
async def get_chat(
    auth: Auth,
    chat_svc: Annotated[ChatService, Depends(ChatService.inject_svc)],
    slug: str,
) -> Chat:
    chat = await chat_svc.get_chat_by_slug(slug, auth.user_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    messages, new_cursor = await chat_svc.get_chat_messages(chat_id=chat.id)
    return Chat(
        id=chat.id,
        title=chat.title,
        slug=chat.slug,
        messages=Paginated(
            items=[ChatMessage.model_validate(message) for message in messages],
            cursor=new_cursor,
        ),
    )


@router.get("/{slug}/messages")
async def get_chat_messages(
    auth: Auth,
    chat_svc: Annotated[ChatService, Depends(ChatService.inject_svc)],
    slug: str,
    cursor: int = 0,
) -> Paginated[ChatMessage]:
    chat = await chat_svc.get_chat_by_slug(slug, auth.user_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    messages, new_cursor = await chat_svc.get_chat_messages(
        chat_id=chat.id, offset=cursor
    )
    return Paginated(
        items=[ChatMessage.model_validate(message) for message in messages],
        cursor=new_cursor,
    )
