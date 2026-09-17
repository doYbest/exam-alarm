import asyncio
from pathlib import Path

from app.core.providers import embedding_provider
from app.db.session import SessionLocal
from app.knowledge.importer import import_manifest


async def main() -> None:
    root = Path(__file__).resolve().parents[3] / "knowledge"
    provider = embedding_provider()
    async with SessionLocal() as session:
        for path in sorted((root / "manifests").glob("*.yaml")):
            changed = await import_manifest(session, path, root, provider)
            print(f"{path.name}: {'imported' if changed else 'unchanged'}")


if __name__ == "__main__":
    asyncio.run(main())
