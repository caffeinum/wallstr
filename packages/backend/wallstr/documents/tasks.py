from uuid import UUID

import structlog
from dramatiq.middleware import CurrentMessage

from wallstr.conf import settings
from wallstr.documents.models import DocumentStatus
from wallstr.documents.services import DocumentService
from wallstr.documents.unstructured import upload_document_to_weaviate
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

    document_svc = DocumentService(db_session)

    document = await document_svc.get_document(UUID(document_id))
    if not document:
        raise Exception("Document not found")

    if document.status != DocumentStatus.UPLOADED:
        raise Exception("Document is not uploaded")

    remote_url = f"s3://{settings.STORAGE_BUCKET}/{document.storage_path}"
    await upload_document_to_weaviate(remote_url, collection_name="Documents")
