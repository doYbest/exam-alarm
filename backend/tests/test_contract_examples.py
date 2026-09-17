import json
from pathlib import Path

import pytest
from pydantic import BaseModel

from app.schemas.api import (
    ApiError,
    BriefingResponse,
    ChatResponse,
    FeedbackResponse,
    HealthResponse,
    HotspotDetail,
    HotspotList,
)

EXAMPLES = Path(__file__).resolve().parents[2] / "contracts/examples"


@pytest.mark.parametrize(
    ("filename", "schema"),
    [
        ("health-success.json", HealthResponse),
        ("health-error.json", ApiError),
        ("hotspots-success.json", HotspotList),
        ("hotspots-error.json", ApiError),
        ("hotspot-detail-success.json", HotspotDetail),
        ("hotspot-detail-error.json", ApiError),
        ("briefing-success.json", BriefingResponse),
        ("briefing-error.json", ApiError),
        ("chat-success.json", ChatResponse),
        ("chat-error.json", ApiError),
        ("feedback-success.json", FeedbackResponse),
        ("feedback-error.json", ApiError),
    ],
)
def test_contract_example_validates(filename: str, schema: type[BaseModel]) -> None:
    schema.model_validate(json.loads((EXAMPLES / filename).read_text(encoding="utf-8")))
