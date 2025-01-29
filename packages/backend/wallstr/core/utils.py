import base64
from uuid import uuid4


def generate_unique_slug(length: int = 12) -> str:
    random_uuid = uuid4()
    base64_slug = (
        base64.urlsafe_b64encode(random_uuid.bytes).decode("utf-8").rstrip("=")
    )
    return base64_slug[:length]
