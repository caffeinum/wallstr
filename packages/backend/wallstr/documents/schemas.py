from uuid import UUID

from pydantic import BaseModel, ConfigDict, computed_field

from wallstr.core.schemas import SSE
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


class DocumentStatusSSE(SSE):
    id: UUID
    status: DocumentStatus

    @computed_field
    def type(self) -> str:
        return "document_status"


class DocumentSection(BaseModel):
    document_title: str
    document_url: str
    page_number: int
    bbox: tuple[float, float, float, float]
