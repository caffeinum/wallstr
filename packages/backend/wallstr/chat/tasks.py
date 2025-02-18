from textwrap import indent
from uuid import UUID, uuid4

import structlog
from dramatiq.middleware import CurrentMessage
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from sqlalchemy import sql
from sqlalchemy.ext.asyncio import AsyncSession
from weaviate.classes.query import Filter, MetadataQuery
from weaviate.collections.classes.internal import Object
from weaviate.collections.classes.types import WeaviateProperties

from wallstr.chat.models import ChatMessageModel, ChatMessageRole
from wallstr.chat.schemas import (
    ChatMessageEndSSE,
    ChatMessageSSE,
    ChatMessageStartSSE,
)
from wallstr.chat.services import ChatService
from wallstr.conf import settings
from wallstr.documents.weaviate import get_weaviate_client
from wallstr.logging import debug
from wallstr.worker import dramatiq

logger = structlog.get_logger()


@dramatiq.actor  # type: ignore
async def process_chat_message(
    message_id: str, openai_model: str = "chatgpt-4o-latest"
) -> None:
    ctx = CurrentMessage.get_current_message()
    if not ctx:
        raise Exception("No ctx message")

    db_session = ctx.options.get("session")
    if not db_session:
        raise Exception("No session")

    chat_svc = ChatService(db_session)
    message = await chat_svc.get_chat_message(UUID(message_id))
    if not message:
        raise Exception("Message not found")

    if not message.content:
        # Not reply on an empty message
        return

    redis = ctx.options.get("redis")
    if not redis:
        raise Exception("No redis")

    topic = f"{message.user_id}:{message.chat_id}:{message.id}"
    new_message_id = uuid4()
    await redis.publish(topic, ChatMessageStartSSE(id=new_message_id).model_dump_json())

    llm = ChatOpenAI(api_key=settings.OPENAI_API_KEY, model=openai_model)
    document_ids = await chat_svc.get_chat_document_ids(message.chat_id)
    llm_context = await get_llm_context(db_session, document_ids, message)
    chunks: list[str] = []
    async for chunk in llm.astream(
        [*llm_context, HumanMessage(content=message.content)]
    ):
        if not chunk.content:
            continue
        chunk_content = chunk.content
        if not isinstance(chunk_content, str):
            # TODO: don't output dict content when type handled
            logger.error(f"Chunk content is not a string {chunk_content}")
            continue
        # strip leading new line on the start of the message
        # TODO: use langchain BaseChunk merging
        chunks.append(chunk_content.lstrip()) if len(chunks) == 0 else chunks.append(
            chunk_content
        )
        await redis.publish(
            topic,
            ChatMessageSSE(id=new_message_id, content=chunk_content).model_dump_json(),
        )
    new_message = await chat_svc.create_chat_message(
        chat_id=message.chat_id,
        message="".join(chunks),
        role=ChatMessageRole.ASSISTANT,
    )
    debug("".join(chunks))

    await redis.publish(
        topic,
        ChatMessageEndSSE(
            id=new_message_id,
            new_id=new_message.id,
            created_at=new_message.created_at,
            content=new_message.content,
        ).model_dump_json(),
    )


async def get_llm_context(
    db_session: AsyncSession, document_ids: list[UUID], message: ChatMessageModel
) -> list[SystemMessage | HumanMessage | AIMessage]:
    llm_context: list[SystemMessage | HumanMessage | AIMessage] = [
        SystemMessage(SYSTEM_PROMPT),
        *await get_prompts_examples(message),
        *await get_rag(document_ids, message),
        HumanMessage(content=message.content),
    ]

    debug(llm_context)
    return list(llm_context)


async def get_history(
    db_session: AsyncSession, message: ChatMessageModel, limit: int = 15
) -> list[AIMessage]:
    """
    Retrieves last messages from the chat to provide context to the LLM.
    """
    async with db_session.begin():
        result = await db_session.execute(
            sql.select(ChatMessageModel)
            .filter_by(chat_id=message.chat_id, deleted_at=None)
            .where(
                ChatMessageModel.created_at < message.created_at,
            )
            .order_by(ChatMessageModel.created_at.desc())
            .limit(limit)
        )
    messages = result.scalars().all()
    return [AIMessage(content=message.content) for message in messages]


async def get_rag(
    document_ids: list[UUID], message: ChatMessageModel
) -> list[HumanMessage]:
    wvc = get_weaviate_client(with_openai=True)
    await wvc.connect()
    try:
        # Check if user's tenant exists
        tenant_id = str(message.user_id)
        if not await wvc.collections.get("Documents").tenants.get_by_names([tenant_id]):
            return []

        collection = wvc.collections.get("Documents").with_tenant(tenant_id)
        response = await collection.query.near_text(
            filters=Filter.by_property("document_id").contains_any(document_ids)
            if document_ids
            else None,
            query=message.content,
            certainty=0.7,
            limit=50,
            return_metadata=MetadataQuery(distance=True, certainty=True),
        )
        debug(response.objects)

        context = "\n".join([_get_rag_line(prompt) for prompt in response.objects])
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


async def get_prompts_examples(message: ChatMessageModel) -> list[SystemMessage]:
    wvc = get_weaviate_client(with_openai=True)
    await wvc.connect()
    try:
        collection = wvc.collections.get("Prompts")
        response = await collection.query.near_text(
            query=message.content,
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


SYSTEM_PROMPT = """
You are a highly precise financial analysis AI specializing in institutional banking, investment research, and financial document interpretation. Your role is to extract, analyze, and structure key financial insights **only from the provided documents**—do not use model knowledge or external data.  
Response Criteria
1. Clarity: Each sentence conveys a single, well-defined idea.
2. Conciseness: Deliver insights using the fewest words necessary.
3. Objectivity: Use a neutral tone without speculation or opinion.
4. Data-Driven Analysis: Every claim must be backed by exact figures from the document.
5. Specificity: Include precise metrics, timeframes, and absolute numbers.
6. Structure: Each sentence should express one key point for readability.
7. Consistency: Use standardized financial terminology and formatting.
8. Active Voice: Attribute actions explicitly (e.g., "Company X increased revenue…").
9. Logical Flow: Connect insights with clear transitions for coherence.
10. Precision: Avoid ambiguity, redundancy, and vague phrasing.
11. Comparative Accuracy: When comparing data, define reference points.
12. Relative & Absolute Figures: Pair percentage changes with corresponding values.
13. Time Frames: Always specify the period of analysis.
14. Visual Aids: Use tables where appropriate for dense data representation.
Example Response (Using Document Data)
"Company X's Q3 2023 revenue increased by 18% YoY to $5.2 billion, driven by a 25% rise in cloud services demand."
"Company X performed well this quarter with strong revenue growth." (Vague, lacks data and timeframe)
Your analysis must strictly follow these guidelines and only reference data found in the uploaded documents.

Output with Markdown format.
When you generate a response include in the significant parts referenes to the RAG Context chunks it's based on as links.
For example:
Some text here. [source](id), where #id is the id of the RAG Context chunk.
"Company X's Q3 2023 revenue [increased by 18% YoY to $5.2 billion](id1,id2), [driven by a 25% rise in cloud services demand](id3)"
"""
