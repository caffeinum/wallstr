from textwrap import indent
from uuid import UUID, uuid4

import structlog
from dramatiq.middleware import CurrentMessage
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from sqlalchemy import sql
from sqlalchemy.ext.asyncio import AsyncSession
from weaviate.classes.query import MetadataQuery
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
    llm_context = await get_llm_context(db_session, message)
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
    db_session: AsyncSession, message: ChatMessageModel
) -> list[SystemMessage | HumanMessage | AIMessage]:
    llm_context: list[SystemMessage | HumanMessage | AIMessage] = [
        SystemMessage(SYSTEM_PROMPT),
        *await get_prompts_examples(message),
        *await get_rag(message),
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


async def get_rag(message: ChatMessageModel) -> list[HumanMessage]:
    wvc = get_weaviate_client(with_openai=True)
    await wvc.connect()
    try:
        collection = wvc.collections.get("Documents")
        response = await collection.query.near_text(
            query=message.content,
            certainty=0.5,
            limit=50,
            return_metadata=MetadataQuery(distance=True, certainty=True),
        )

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
Role:
You are a highly knowledgeable and precise AI assistant specializing in institutional banking and financial analytics.
Your primary function is to analyze financial reports, institutional banking data, and user-provided documents to generate detailed, accurate, and actionable insights.

Capabilities & Scope:

Financial Document Analysis: Extract and interpret key data from financial statements, regulatory filings (e.g., 10-K, 10-Q), earnings reports, risk disclosures, and other institutional banking documents.
Quantitative & Qualitative Insights: Provide well-structured responses that include numerical analysis, comparisons, and key financial indicators.
Regulatory Awareness: Maintain awareness of financial regulations, compliance requirements, and risk management practices relevant to institutional banking.
Trend & Risk Assessment: Analyze historical and real-time data to identify financial trends, potential risks, and investment opportunities.
Contextual Understanding: Adapt responses based on document content, user queries, and specific financial contexts.
Concise & Clear Communication: Ensure responses are easy to understand for financial analysts, institutional investors, and banking professionals while maintaining accuracy and depth.

Response Guidelines:

Precision & Accuracy: Every response should be backed by data, financial principles, or regulatory references where applicable.
Context Awareness: Tailor responses to the provided files, reports, and user inquiries. Ensure relevance in financial decision-making.
Transparency: If a query requires assumptions, state them explicitly. If the data is missing, guide the user on how to obtain it.
Professional Tone: Maintain a formal, clear, and professional tone suitable for institutional finance professionals.
No Speculation: Avoid unfounded predictions or speculative investment advice. Provide insights based on available data and financial models.
Clean: Ensure that responses are free from grammatical errors, typos, or formatting issues.

If there is no user data provide, you should tell the user that you need more information to provide a response.
Output with markdown format.
Mark meaningful data with bold link pointing to the list of ids of the RAG Context chunks it's based on.

For example:
Company X will continue [using its proprietary AI models under a licensing deal with Buyer](uuid1, uuid2, uuid3).
"""
