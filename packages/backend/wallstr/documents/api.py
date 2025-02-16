from typing import Annotated
from uuid import UUID

import boto3
import botocore.config
from fastapi import APIRouter, Depends, HTTPException, Request, status
from weaviate.classes.query import Filter

from wallstr.auth.dependencies import Auth
from wallstr.auth.schemas import HTTPUnauthorizedError
from wallstr.conf import settings
from wallstr.documents.schemas import DocumentSection
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


@router.get("/section/{section_id}")
async def get_document_by_section(
    request: Request,
    auth: Auth,
    section_id: UUID,
    document_svc: Annotated[DocumentService, Depends(DocumentService.inject_svc)],
) -> DocumentSection:
    wvc = request.state.wvc

    collection = wvc.collections.get("Documents")
    response = await collection.query.fetch_objects(
        filters=(
            Filter.by_id().equal(section_id)
            & Filter.by_property("user_id").equal(auth.user_id)
        ),
        limit=1,
    )
    if not response.objects:
        raise HTTPException(status_code=404, detail="Section not found")

    chunk = response.objects[0]
    document = await document_svc.get_document(chunk.properties["document_id"])
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    s3_client = boto3.client(
        "s3",
        endpoint_url=str(settings.STORAGE_URL),
        aws_access_key_id=settings.STORAGE_ACCESS_KEY.get_secret_value(),
        aws_secret_access_key=settings.STORAGE_SECRET_KEY.get_secret_value(),
        config=botocore.config.Config(signature_version="s3v4"),
    )
    document_url = s3_client.generate_presigned_url(
        ClientMethod="get_object",
        Params={
            "Bucket": settings.STORAGE_BUCKET,
            "Key": document.storage_path,
        },
        ExpiresIn=60 * 5,
    )

    section = DocumentSection(
        document_title=document.filename,
        document_url=document_url,
        page_number=chunk.properties["metadata"]["page_number"],
        bbox=(1, 1, 1, 1),
    )

    return section
