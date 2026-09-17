from datetime import UTC, datetime
from uuid import uuid4

import httpx
import pytest
from fastapi import HTTPException

from app.api.common import cached_json
from app.api.hotspots import decode_cursor, encode_cursor, time_bounds
from app.main import app


async def test_hotspots_requires_alpha_token() -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/v1/hotspots")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
    assert response.headers["X-Request-ID"]


def test_etag_revalidation() -> None:
    response = cached_json({"items": []}, None)
    etag = response.headers["ETag"]
    assert cached_json({"items": []}, etag).status_code == 304


def test_cursor_round_trip_and_invalid_cursor() -> None:
    at = datetime.now(UTC)
    event_id = uuid4()
    assert decode_cursor(encode_cursor(at, event_id)) == (at, event_id)
    with pytest.raises(HTTPException):
        decode_cursor("invalid")


def test_local_day_bounds_use_zone_not_fixed_utc() -> None:
    from datetime import date, timedelta

    start, end = time_bounds(date(2026, 9, 17), "Asia/Shanghai")
    assert start.hour == 16
    assert end - start == timedelta(days=1)
