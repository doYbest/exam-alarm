from datetime import date

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.knowledge.embedding import EmbeddingProvider
from app.models.content import KnowledgeChunk, KnowledgeDocument


async def search_knowledge(
    session: AsyncSession,
    question: str,
    provider: EmbeddingProvider,
    *,
    exam_scope: str | None = None,
    as_of: date | None = None,
    limit: int = 8,
) -> list[tuple[KnowledgeChunk, KnowledgeDocument]]:
    if not 1 <= limit <= 8:
        raise ValueError("limit must be between 1 and 8")
    query = await provider.embed(question)
    statement = (
        select(KnowledgeChunk, KnowledgeDocument)
        .join(KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id)
        .where(KnowledgeDocument.status == "active")
        .where(KnowledgeChunk.embedding_model == provider.model_name)
    )
    if exam_scope:
        statement = statement.where(KnowledgeDocument.exam_scope.contains([exam_scope]))
    if as_of:
        statement = statement.where(
            or_(
                KnowledgeDocument.effective_from.is_(None),
                KnowledgeDocument.effective_from <= as_of,
            ),
            or_(KnowledgeDocument.effective_to.is_(None), KnowledgeDocument.effective_to >= as_of),
        )
    statement = statement.order_by(KnowledgeChunk.embedding.cosine_distance(query)).limit(limit)
    result = await session.execute(statement)
    return list(result.tuples().all())
