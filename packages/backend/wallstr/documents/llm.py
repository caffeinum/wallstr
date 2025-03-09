from textwrap import indent
from uuid import UUID

import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from weaviate.classes.query import Filter, MetadataQuery
from weaviate.collections.classes.internal import Object
from weaviate.collections.classes.types import WeaviateProperties

from wallstr.documents.weaviate import get_weaviate_client
from wallstr.logging import debug

logger = structlog.get_logger()


async def get_rag(
    document_ids: list[UUID],
    user_id: UUID,
    content: str,
    *,
    distance: float = 0.73,
    limit: int = 50,
    soft_limit: int | None = None,
    soft_distance: float | None = None,
) -> list[HumanMessage]:
    """
    Output finded RAG context for the given document_ids and user_id.
    soft_limit allows to request minimum numbers of sections, when the distance > soft_distance
    """
    if not document_ids:
        return []
    wvc = get_weaviate_client(with_openai=True)
    await wvc.connect()
    try:
        # Check if user's tenant exists
        tenant_id = str(user_id)
        collection = wvc.collections.get("Documents")
        if not await collection.tenants.get_by_names([tenant_id]):
            logger.info(f"Tenant {tenant_id} not found")
            return []

        response = await collection.with_tenant(tenant_id).query.near_text(
            filters=Filter.by_property("document_id").contains_any(document_ids),
            query=content,
            distance=distance,
            limit=limit,
            return_metadata=MetadataQuery(distance=True),
        )
        objects = response.objects
        debug(objects)
        logger.info(f"RAG matches: {len(objects)}")
        if soft_limit and soft_distance and len(objects) > soft_limit:
            objects = [
                *objects[:soft_limit],
                *[obj for obj in objects if obj.metadata.distance < soft_distance],
            ]
            logger.info(f"RAG matches with soft_limit: {len(objects)}")

        context = "\n".join([_get_rag_line(prompt) for prompt in objects])
        if not context:
            return []
        return [
            HumanMessage(f"# RAG Context\n{context}"),
        ]
    finally:
        await wvc.close()


def _get_rag_line(chunk: Object[WeaviateProperties, None]) -> str:
    text = str(chunk.properties["text"])
    return f"""
    ## id: {chunk.uuid}
    {indent(text, " " * 4)}
    """


async def get_prompts_examples(prompt: str) -> list[SystemMessage]:
    wvc = get_weaviate_client(with_openai=True)
    await wvc.connect()
    try:
        collection = wvc.collections.get("Prompts")
        response = await collection.query.near_text(
            query=prompt,
            certainty=0.5,
            limit=10,
        )
        return [
            SystemMessage(f"""
        Example of response you provide:
        {"\n".join([f"- {prompt.properties["reply"]}" for prompt in response.objects])}
        """)
        ]
    finally:
        await wvc.close()
