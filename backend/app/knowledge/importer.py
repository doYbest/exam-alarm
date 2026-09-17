import hashlib
from datetime import date
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.knowledge.embedding import EmbeddingProvider
from app.models.content import KnowledgeChunk, KnowledgeDocument

DocumentType = Literal[
    "exam_outline",
    "exam_point",
    "official_question",
    "policy_material",
    "editorial_rule",
    "example_material",
]


class KnowledgeManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    external_id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1)
    document_type: DocumentType
    exam_scope: list[str] = Field(min_length=1)
    source_url: str | None = None
    license_note: str = Field(min_length=1)
    effective_from: date | None = None
    effective_to: date | None = None
    tags: list[str] = Field(default_factory=list)
    file: str

    @model_validator(mode="after")
    def check_effective_dates(self) -> "KnowledgeManifest":
        if self.effective_to and self.effective_from and self.effective_to < self.effective_from:
            raise ValueError("effective_to precedes effective_from")
        return self


def read_manifest(path: Path, knowledge_root: Path) -> tuple[KnowledgeManifest, str]:
    root = knowledge_root.resolve()
    manifest = KnowledgeManifest.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    content_path = (path.parent / manifest.file).resolve()
    if not content_path.is_relative_to(root):
        raise ValueError("knowledge file must stay inside knowledge root")
    content = content_path.read_text(encoding="utf-8").strip()
    if not content:
        raise ValueError("knowledge file is empty")
    return manifest, content


def chunk_text(text: str, target: int = 700, overlap: int = 120) -> list[str]:
    if target <= overlap or overlap < 0:
        raise ValueError("target must exceed nonnegative overlap")
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + target, len(text))
        if end < len(text):
            paragraph_break = text.rfind("\n\n", start + target // 2, end)
            if paragraph_break > start:
                end = paragraph_break
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        start = max(start + 1, end - overlap)
    return chunks


async def import_manifest(
    session: AsyncSession, path: Path, knowledge_root: Path, provider: EmbeddingProvider
) -> bool:
    manifest, content = read_manifest(path, knowledge_root)
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    existing = await session.scalar(
        select(KnowledgeDocument).where(KnowledgeDocument.external_id == manifest.external_id)
    )
    if existing and existing.content_hash == content_hash:
        models = set(
            (
                await session.scalars(
                    select(KnowledgeChunk.embedding_model).where(
                        KnowledgeChunk.document_id == existing.id
                    )
                )
            ).all()
        )
        if models == {provider.model_name}:
            return False
    document = existing or KnowledgeDocument(external_id=manifest.external_id)
    if existing:
        await session.execute(
            delete(KnowledgeChunk).where(KnowledgeChunk.document_id == existing.id)
        )
        document.version += 1
    else:
        document.version = 1
        session.add(document)
    document.title = manifest.title
    document.document_type = manifest.document_type
    document.exam_scope = manifest.exam_scope
    document.source_url = manifest.source_url
    document.license_note = manifest.license_note
    document.effective_from = manifest.effective_from
    document.effective_to = manifest.effective_to
    document.content_hash = content_hash
    document.status = "active"
    document.metadata_json = {"tags": manifest.tags}
    await session.flush()
    for index, chunk in enumerate(chunk_text(content)):
        session.add(
            KnowledgeChunk(
                document_id=document.id,
                chunk_index=index,
                text=chunk,
                token_count=len(chunk),
                tags=manifest.tags,
                embedding=await provider.embed(chunk),
                embedding_model=provider.model_name,
                metadata_json={},
            )
        )
    await session.commit()
    return True
