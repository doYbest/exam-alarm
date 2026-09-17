from uuid import uuid4

import pytest

from app.briefing.generate import Candidate, select_candidates


def candidate(category: str, score: int = 85, eligible: bool = True) -> Candidate:
    return Candidate(uuid4(), uuid4(), category, score, eligible, "自写示例晨报内容")


def test_selects_three_with_category_diversity() -> None:
    first = candidate("公共管理", 95)
    second = candidate("公共管理", 90)
    third_same_category = candidate("公共管理", 89)
    fourth = candidate("经济", 85)
    selected = select_candidates([fourth, third_same_category, second, first])
    assert selected == [first, second, fourth]


def test_insufficient_safe_candidates_does_not_publish_briefing() -> None:
    assert select_candidates([candidate("公共管理"), candidate("经济", eligible=False)]) == []


def test_count_limits() -> None:
    with pytest.raises(ValueError):
        select_candidates([], count=2)
