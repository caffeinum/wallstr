from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from wallstr.auth.dependencies import Auth
from wallstr.auth.schemas import HTTPUnauthorizedError
from wallstr.documents.services import DocumentService
from wallstr.documents.tasks import process_document
from wallstr.openapi import generate_unique_id_function

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    generate_unique_id_function=generate_unique_id_function(3),
    responses={401: {"model": HTTPUnauthorizedError}},
)


@router.put(
    "/{id}/mark-uploaded",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Mark document as uploaded",
)
async def mark_document_uploaded(
    auth: Auth,
    id: UUID,
    document_svc: Annotated[DocumentService, Depends(DocumentService.inject_svc)],
) -> None:
    await document_svc.mark_document_uploaded(auth.user_id, id)
    process_document.send(document_id=str(id))
