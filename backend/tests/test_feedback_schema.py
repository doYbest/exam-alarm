from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.api import FeedbackRequest


def test_feedback_requires_timezone_and_bounded_batch() -> None:
    item = {
        "client_event_id": str(uuid4()),
        "hotspot_id": str(uuid4()),
        "event_type": "click",
        "occurred_at": datetime.now(UTC).isoformat(),
    }
    assert len(FeedbackRequest.model_validate({"events": [item]}).events) == 1
    with pytest.raises(ValidationError):
        FeedbackRequest.model_validate({"events": [{**item, "occurred_at": "2026-09-17T09:00:00"}]})
    with pytest.raises(ValidationError):
        FeedbackRequest.model_validate({"events": [item] * 101})
