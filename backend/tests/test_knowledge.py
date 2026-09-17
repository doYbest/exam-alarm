from pathlib import Path

import pytest

from app.knowledge.embedding import EMBEDDING_DIMENSION, MockEmbeddingProvider
from app.knowledge.importer import chunk_text, read_manifest


def test_manifest_references_local_authored_content() -> None:
    root = Path(__file__).resolve().parents[2] / "knowledge"
    manifest, content = read_manifest(root / "manifests/kb-gov-001.yaml", root)
    assert manifest.license_note == "internally-authored-example"
    assert "本材料为自写示例" in content


def test_chunking_covers_tail_and_rejects_bad_overlap() -> None:
    text = "甲" * 1500
    chunks = chunk_text(text)
    assert chunks[-1].endswith("甲")
    assert len(chunks) >= 2
    with pytest.raises(ValueError):
        chunk_text(text, target=100, overlap=100)


async def test_mock_embedding_is_repeatable_and_dimensioned() -> None:
    provider = MockEmbeddingProvider()
    first = await provider.embed("基层公共服务")
    assert first == await provider.embed("基层公共服务")
    assert len(first) == EMBEDDING_DIMENSION
