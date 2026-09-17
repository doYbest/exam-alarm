from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.ai.schema import analysis_input_hash, validate_analysis


def sample_response() -> dict[str, object]:
    paragraph = (
        "该示例事件涉及基层服务流程。分析时应核对发布主体、适用范围和实施时间，并关注群众办事体验。"
    )
    return {
        "scores": {
            "exam_relevance": 26,
            "clear_test_point": 17,
            "public_affairs": 13,
            "timeliness": 8,
            "source_reliability": 9,
            "trend_linkage": 3,
            "essay_interview_value": 9,
        },
        "category": "公共管理",
        "subcategories": ["基层治理"],
        "exam_types": ["申论", "面试"],
        "reason": "与基层公共服务直接相关。",
        "brief": "某地公布基层公共服务流程优化方案，考公可关注服务可及性、执行与效果评估。",
        "summary": paragraph * 4,
        "deep_analysis": {
            "background": paragraph * 4,
            "what_changed": paragraph * 3,
            "why_it_matters": paragraph * 2,
            "exam_relevance": paragraph * 2,
            "possible_angles": ["服务可及性", "执行评估"],
        },
        "key_points": ["核实适用范围"],
        "knowledge_refs": ["knowledge-1"],
        "evidence_refs": ["article-1"],
        "insufficient_evidence": False,
        "safety_flags": [],
    }


def test_total_is_server_computed_and_briefing_threshold_applies() -> None:
    raw = sample_response()
    raw["total_score"] = 0
    result = validate_analysis(
        raw, allowed_knowledge_refs={"knowledge-1"}, allowed_evidence_refs={"article-1"}
    )
    assert result.total_score == 85
    assert result.include_in_briefing
    assert result.importance == "core"


def test_forged_reference_is_rejected() -> None:
    raw = sample_response()
    raw["evidence_refs"] = ["forged"]
    with pytest.raises(ValueError, match="unknown news"):
        validate_analysis(
            raw, allowed_knowledge_refs={"knowledge-1"}, allowed_evidence_refs={"article-1"}
        )


def test_source_reliability_cannot_exceed_source_configuration() -> None:
    with pytest.raises(ValueError, match="source reliability"):
        validate_analysis(
            sample_response(),
            allowed_knowledge_refs={"knowledge-1"},
            allowed_evidence_refs={"article-1"},
            source_reliability_cap=5,
        )


def test_out_of_range_and_extra_fields_are_rejected() -> None:
    raw = sample_response()
    scores = deepcopy(raw["scores"])
    assert isinstance(scores, dict)
    scores["exam_relevance"] = 31
    raw["scores"] = scores
    with pytest.raises(ValidationError):
        validate_analysis(
            raw, allowed_knowledge_refs={"knowledge-1"}, allowed_evidence_refs={"article-1"}
        )
    raw = sample_response()
    raw["unsupported"] = "value"
    with pytest.raises(ValidationError):
        validate_analysis(
            raw, allowed_knowledge_refs={"knowledge-1"}, allowed_evidence_refs={"article-1"}
        )


def test_input_hash_changes_with_evidence() -> None:
    first = analysis_input_hash("event", ["a"], ["hash-a"], ["k"])
    second = analysis_input_hash("event", ["a", "b"], ["hash-a", "hash-b"], ["k"])
    assert first != second
