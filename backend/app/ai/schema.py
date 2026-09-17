import hashlib
import json
from dataclasses import dataclass
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

Category = Literal["公共管理", "经济", "科技", "社会", "生态", "法治", "文化", "其他"]
ExamType = Literal["行测常识", "申论", "面试"]


class Scores(BaseModel):
    model_config = ConfigDict(extra="forbid")

    exam_relevance: Annotated[StrictInt, Field(ge=0, le=30)]
    clear_test_point: Annotated[StrictInt, Field(ge=0, le=20)]
    public_affairs: Annotated[StrictInt, Field(ge=0, le=15)]
    timeliness: Annotated[StrictInt, Field(ge=0, le=10)]
    source_reliability: Annotated[StrictInt, Field(ge=0, le=10)]
    trend_linkage: Annotated[StrictInt, Field(ge=0, le=5)]
    essay_interview_value: Annotated[StrictInt, Field(ge=0, le=10)]

    @property
    def total(self) -> int:
        return sum(self.model_dump().values())


class DeepAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    background: str
    what_changed: str
    why_it_matters: str
    exam_relevance: str
    possible_angles: list[str]


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scores: Scores
    category: Category
    subcategories: list[str]
    exam_types: list[ExamType]
    reason: str
    brief: str = Field(min_length=30, max_length=80)
    summary: str = Field(min_length=150, max_length=300)
    deep_analysis: DeepAnalysis
    key_points: list[str]
    knowledge_refs: list[str]
    evidence_refs: list[str]
    insufficient_evidence: bool
    safety_flags: list[str]

    @model_validator(mode="after")
    def check_evidence_consistency(self) -> "AnalysisResponse":
        if self.insufficient_evidence and self.deep_analysis.possible_angles:
            raise ValueError("possible exam angles require sufficient evidence")
        deep_length = sum(
            len(value) if isinstance(value, str) else sum(map(len, value))
            for value in self.deep_analysis.model_dump().values()
        )
        if not 500 <= deep_length <= 1200:
            raise ValueError("deep analysis is outside expected length")
        return self


@dataclass(frozen=True)
class ValidatedAnalysis:
    response: AnalysisResponse
    total_score: int
    include_in_hotlist: bool
    include_in_briefing: bool
    importance: str | None


def validate_analysis(
    raw: dict[str, object],
    *,
    allowed_knowledge_refs: set[str],
    allowed_evidence_refs: set[str],
    source_reliability_cap: int | None = None,
) -> ValidatedAnalysis:
    # A model-provided total is discarded; the authoritative score is computed below.
    payload = {key: value for key, value in raw.items() if key != "total_score"}
    response = AnalysisResponse.model_validate(payload)
    if (
        source_reliability_cap is not None
        and response.scores.source_reliability > source_reliability_cap
    ):
        raise ValueError("source reliability exceeds configured source score")
    if not set(response.knowledge_refs) <= allowed_knowledge_refs:
        raise ValueError("analysis cites unknown knowledge chunks")
    if not set(response.evidence_refs) <= allowed_evidence_refs:
        raise ValueError("analysis cites unknown news articles")
    if len(response.evidence_refs) != len(set(response.evidence_refs)):
        raise ValueError("duplicate evidence references")
    has_evidence = bool(response.evidence_refs) and not response.insufficient_evidence
    safe = not response.safety_flags
    total = response.scores.total
    hotlist = total >= 50 and has_evidence and safe
    briefing = hotlist and total >= 80 and response.scores.source_reliability >= 7
    importance = "core" if total >= 65 else "other" if hotlist else None
    return ValidatedAnalysis(response, total, hotlist, briefing, importance)


def analysis_input_hash(
    event_id: str, article_ids: list[str], article_hashes: list[str], knowledge_ids: list[str]
) -> str:
    payload = json.dumps(
        {
            "event_id": event_id,
            "article_ids": sorted(article_ids),
            "article_hashes": sorted(article_hashes),
            "knowledge_ids": sorted(knowledge_ids),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
