from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QueryRoute:
    intent: str
    preferred_content_types: tuple[str, ...] = ()
    preferred_document_kinds: tuple[str, ...] = ()
    prefer_question_opening: bool = False


INTERVIEW_KEYWORDS = (
    "面试",
    "八股",
    "常见题",
    "高频题",
    "怎么回答",
    "如何回答",
    "回答思路",
)

CONCEPT_KEYWORDS = (
    "什么是",
    "是什么",
    "定义",
    "原理",
    "作用",
    "区别",
    "为什么",
    "优缺点",
    "特点",
)

DESIGN_KEYWORDS = (
    "系统设计",
    "架构",
    "设计",
    "trade-off",
    "权衡",
    "高可用",
    "扩展性",
    "方案",
)

IMPLEMENTATION_KEYWORDS = (
    "实现",
    "落地",
    "接口",
    "流程",
    "步骤",
    "配置",
    "部署",
    "代码",
    "怎么做",
    "如何做",
)


def classify_query_route(question: str) -> QueryRoute:
    normalized = question.strip().lower()
    if not normalized:
        return QueryRoute(intent="general")

    scores = {
        "interview": _count_keyword_hits(normalized, INTERVIEW_KEYWORDS),
        "concept": _count_keyword_hits(normalized, CONCEPT_KEYWORDS),
        "design": _count_keyword_hits(normalized, DESIGN_KEYWORDS),
        "implementation": _count_keyword_hits(normalized, IMPLEMENTATION_KEYWORDS),
    }

    if normalized.endswith("?") or normalized.endswith("？"):
        scores["concept"] += 1

    if "区别" in normalized or "为什么" in normalized:
        scores["concept"] += 1

    best_intent, best_score = max(scores.items(), key=lambda item: item[1], default=("general", 0))
    if best_score <= 0:
        return QueryRoute(intent="general")

    if best_intent == "interview":
        return QueryRoute(
            intent="interview",
            preferred_content_types=("question_answer",),
            preferred_document_kinds=("interview_qa",),
            prefer_question_opening=True,
        )
    if best_intent == "concept":
        return QueryRoute(
            intent="concept",
            preferred_content_types=("concept_explanation", "question_answer"),
            preferred_document_kinds=("concept_guide", "interview_qa"),
        )
    if best_intent == "design":
        return QueryRoute(
            intent="design",
            preferred_content_types=("design_discussion", "example_driven"),
            preferred_document_kinds=("design_notes", "project_review"),
        )
    if best_intent == "implementation":
        return QueryRoute(
            intent="implementation",
            preferred_content_types=("implementation_detail", "example_driven"),
            preferred_document_kinds=("project_review", "concept_guide"),
        )
    return QueryRoute(intent="general")


def build_query_plan(route: QueryRoute) -> list[dict[str, object]]:
    plan: list[dict[str, object]] = []

    for content_type in route.preferred_content_types:
        plan.append({"content_type_hint": content_type})

    for document_kind in route.preferred_document_kinds:
        plan.append({"document_kind": document_kind})

    if route.prefer_question_opening:
        plan.append({"starts_with_question": True})

    plan.append({})
    return _deduplicate_plan(plan)


def _count_keyword_hits(text: str, keywords: tuple[str, ...]) -> int:
    return sum(text.count(keyword.lower()) for keyword in keywords)


def _deduplicate_plan(plan: list[dict[str, object]]) -> list[dict[str, object]]:
    deduplicated: list[dict[str, object]] = []
    seen: set[tuple[tuple[str, object], ...]] = set()
    for item in plan:
        normalized = tuple(sorted(item.items()))
        if normalized in seen:
            continue
        seen.add(normalized)
        deduplicated.append(item)
    return deduplicated
