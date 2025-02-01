# /usr/bin/env python
import asyncio

import structlog
from weaviate.classes.config import Configure, DataType, Property

from wallstr.documents.weaviate import get_weaviate_client
from wallstr.logging import configure_logging

configure_logging()

logger = structlog.get_logger()


async def migrate_weaviate() -> None:
    logger.info("Migrating Weaviate")
    wvc = get_weaviate_client()
    await wvc.connect()
    if not await wvc.collections.exists("Documents"):
        logger.info("Creating collection [Documents]")
        await wvc.collections.create(
            "Documents",
            vectorizer_config=Configure.Vectorizer.text2vec_openai(
                model="text-embedding-3-small",
            ),
            properties=[
                Property(name="record_id", data_type=DataType.TEXT),
            ],
        )
    await wvc.close()
    logger.info("Migrating Weaviate done")


if __name__ == "__main__":
    asyncio.run(migrate_weaviate())
