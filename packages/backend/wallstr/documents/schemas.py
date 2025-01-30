from uuid import UUID

from pydantic import BaseModel, ConfigDict

from wallstr.documents.models import DocumentStatus


class PendingDocument(BaseModel):
    id: UUID
    filename: str
    presigned_url: str


class Document(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    status: DocumentStatus
