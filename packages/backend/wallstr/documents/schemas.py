from uuid import UUID

from pydantic import BaseModel


class PendingDocument(BaseModel):
    id: UUID
    filename: str
    presigned_url: str
