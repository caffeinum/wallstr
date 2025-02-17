from uuid import UUID

import structlog
from dramatiq.middleware import CurrentMessage
from structlog.contextvars import bind_contextvars

from wallstr.documents.services import DocumentService
from wallstr.worker import dramatiq

logger = structlog.get_logger()


@dramatiq.actor(priority=10, queue_name="parse")  # type: ignore
async def process_document(document_id: str) -> None:
    ctx = CurrentMessage.get_current_message()
    if not ctx:
        raise Exception("No ctx message")

    bind_contextvars(document_id=document_id, job_id=ctx.message_id)
    logger.info("Processing document")
    db_session = ctx.options.get("session")
    if not db_session:
        raise Exception("No session")

    redis = ctx.options.get("redis")
    if not redis:
        raise Exception("No redis")

    document_svc = DocumentService(db_session, redis)
    await document_svc.parse_document(UUID(document_id))
