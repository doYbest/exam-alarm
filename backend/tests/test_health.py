from typing import Self

import httpx
from pytest import MonkeyPatch
from sqlalchemy.exc import SQLAlchemyError

from app import main


class FakeSession:
    def __init__(self, failing: bool = False) -> None:
        self.failing = failing

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None

    async def execute(self, _query: object) -> None:
        if self.failing:
            raise SQLAlchemyError("database down")


async def test_health_reports_database_status(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(main, "SessionLocal", lambda: FakeSession())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=main.app), base_url="http://test"
    ) as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


async def test_health_fails_when_database_is_unavailable(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(main, "SessionLocal", lambda: FakeSession(failing=True))
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=main.app), base_url="http://test"
    ) as client:
        response = await client.get("/health")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "DATABASE_UNAVAILABLE"
