from uuid import UUID

import structlog
from dramatiq.middleware import CurrentMessage

from wallstr.conf import settings  # type: ignore
from wallstr.documents.models import DocumentStatus
from wallstr.documents.schemas import DocumentStatusSSE
from wallstr.documents.services import DocumentService
from wallstr.documents.unstructured import (
    upload_document_to_weaviate,  # type: ignore
    upload_document_to_weaviate_v2,
)
from wallstr.worker import dramatiq

logger = structlog.get_logger()


@dramatiq.actor  # type: ignore
async def process_document(document_id: str) -> None:
    logger.info("Processing document", document_id=document_id)
    ctx = CurrentMessage.get_current_message()
    if not ctx:
        raise Exception("No ctx message")

    db_session = ctx.options.get("session")
    if not db_session:
        raise Exception("No session")

    redis = ctx.options.get("redis")
    if not redis:
        raise Exception("No redis")

    document_svc = DocumentService(db_session)

    document = await document_svc.get_document(UUID(document_id))
    if not document:
        raise Exception("Document not found")

    if document.status == DocumentStatus.UPLOADING:
        raise Exception("Document is uploading")

    document = await document_svc.mark_document_processing(
        document.user_id, document.id
    )

    topic = f"{document.user_id}:documents:{document.id}"
    await redis.publish(
        topic,
        DocumentStatusSSE(id=document.id, status=document.status).model_dump_json(),
    )

    try:
        # remote_url = f"s3://{settings.STORAGE_BUCKET}/{document.storage_path}"
        # await upload_document_to_weaviate(remote_url, collection_name="Documents")
        await upload_document_to_weaviate_v2(document, collection_name="Documents")
    except Exception:
        # TODO: handle error
        document = await document_svc.mark_document_uploaded(
            document.user_id, document.id
        )
    else:
        document = await document_svc.mark_document_ready(document.user_id, document.id)
    await redis.publish(
        topic,
        DocumentStatusSSE(id=document.id, status=document.status).model_dump_json(),
    )
