from typing import Any
from uuid import UUID

import boto3
import botocore.config
from sqlalchemy import or_, sql

from wallstr.conf import settings
from wallstr.documents.models import DocumentModel, DocumentStatus
from wallstr.services import BaseService


class DocumentService(BaseService):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.s3_client = boto3.client(
            "s3",
            endpoint_url=str(settings.STORAGE_URL),
            aws_access_key_id=settings.STORAGE_ACCESS_KEY.get_secret_value(),
            aws_secret_access_key=settings.STORAGE_SECRET_KEY.get_secret_value(),
            config=botocore.config.Config(signature_version="s3v4"),
        )

    async def get_document(self, document_id: UUID) -> DocumentModel | None:
        async with self.tx():
            result = await self.db.execute(
                sql.select(DocumentModel).filter_by(id=document_id)
            )
        return result.scalar_one_or_none()

    def generate_upload_url(
        self, user_id: UUID, document: DocumentModel, error: str | None = None
    ) -> str:
        if user_id != document.user_id:
            raise ValueError("User is not the owner of the document")

        url = self.s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": settings.STORAGE_BUCKET,
                "Key": document.storage_path,
            },
            ExpiresIn=60 * 5,
        )
        return url

    async def mark_document_uploaded(
        self, user_id: UUID, document_id: UUID
    ) -> DocumentModel:
        async with self.tx():
            result = await self.db.execute(
                sql.update(DocumentModel)
                .filter_by(
                    id=document_id, user_id=user_id, status=DocumentStatus.UPLOADING
                )
                .values(status=DocumentStatus.UPLOADED)
                .returning(DocumentModel)
            )
        return result.scalar_one()

    async def mark_document_processing(
        self, user_id: UUID, document_id: UUID
    ) -> DocumentModel:
        async with self.tx():
            result = await self.db.execute(
                sql.update(DocumentModel)
                .filter_by(id=document_id, user_id=user_id)
                .where(
                    or_(
                        DocumentModel.status == DocumentStatus.UPLOADED,
                        DocumentModel.status == DocumentStatus.PROCESSING,
                        DocumentModel.status == DocumentStatus.READY,
                    )
                )
                .values(status=DocumentStatus.PROCESSING)
                .returning(DocumentModel)
            )
        return result.scalar_one()

    async def mark_document_ready(
        self, user_id: UUID, document_id: UUID
    ) -> DocumentModel:
        async with self.tx():
            result = await self.db.execute(
                sql.update(DocumentModel)
                .filter_by(
                    id=document_id, user_id=user_id, status=DocumentStatus.PROCESSING
                )
                .values(status=DocumentStatus.READY)
                .returning(DocumentModel)
            )
        return result.scalar_one()
