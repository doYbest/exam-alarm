import json
from typing import Protocol


class AIProvider(Protocol):
    model_name: str

    async def complete(self, prompt: str) -> str: ...


class MockAIProvider:
    """Deterministic self-authored demo provider; never use for real news."""

    model_name = "self-authored-demo-v1"

    async def complete(self, prompt: str) -> str:
        request = json.loads(prompt)
        if request.get("mode") != "self_authored_demo":
            raise ValueError("mock provider only accepts self-authored demo inputs")
        paragraph = (
            "本条是自写演示资料，用于检查公考热点分析流程。分析时应核实发布主体、适用范围、"
            "实施时间和原始来源，不能把示例内容当成现实政策。"
        )
        payload = {
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
            "reason": "示例材料涉及公共服务流程与基层执行。",
            "brief": "这是一条自写演示热点，内容涉及公共服务流程，考公可关注执行、服务可及性和效果评估。",
            "summary": paragraph * 4,
            "deep_analysis": {
                "background": paragraph * 4,
                "what_changed": paragraph * 3,
                "why_it_matters": paragraph * 2,
                "exam_relevance": paragraph * 2,
                "possible_angles": ["服务可及性", "执行效果评估"],
            },
            "key_points": ["核实原始资料", "关注执行与评估"],
            "knowledge_refs": request["knowledge_refs"],
            "evidence_refs": request["evidence_refs"],
            "insufficient_evidence": False,
            "safety_flags": [],
        }
        return json.dumps(payload, ensure_ascii=False)
