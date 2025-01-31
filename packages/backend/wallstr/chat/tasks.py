from uuid import UUID

from dramatiq.middleware import CurrentMessage
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import OpenAI
from sqlalchemy import sql
from sqlalchemy.ext.asyncio import AsyncSession

from wallstr.chat.models import ChatMessageModel, ChatMessageRole
from wallstr.chat.services import ChatService
from wallstr.conf import settings
from wallstr.worker import dramatiq


@dramatiq.actor  # type: ignore
async def process_chat_message(message_id: str) -> None:
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

    redis = ctx.options.get("redis")
    if not redis:
        raise Exception("No redis")

    llm = OpenAI(api_key=settings.OPENAI_API_KEY)
    llm_context = await get_llm_context(db_session, message)
    chunks = []
    async for chunk in llm.astream(
        [*llm_context, HumanMessage(content=message.content)]
    ):
        chunks.append(chunk)
        await redis.publish(f"{message.user_id}:{message.chat_id}:{message.id}", chunk)

    await chat_svc.create_chat_message(
        chat_id=message.chat_id,
        message="".join(chunks),
        role=ChatMessageRole.ASSISTANT,
    )


async def get_llm_context(
    db_session: AsyncSession, message: ChatMessageModel, limit: int = 15
) -> list[SystemMessage | HumanMessage | AIMessage]:
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

    llm_context: list[SystemMessage | HumanMessage | AIMessage] = [
        SystemMessage(SYSTEM_PROMPT)
    ]

    for message in messages:
        match message.role:
            case ChatMessageRole.USER:
                llm_context.append(HumanMessage(content=message.content))
            case ChatMessageRole.ASSISTANT:
                llm_context.append(AIMessage(content=message.content))

    return llm_context


SYSTEM_PROMPT = """
Role:
You are a highly knowledgeable and precise AI assistant specializing in institutional banking and financial analytics. Your primary function is to analyze financial reports, institutional banking data, and user-provided documents to generate detailed, accurate, and actionable insights.

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
"""
