from __future__ import annotations

import re

from app.rag.types import LoadedSection


DOCUMENT_KIND_KEYWORDS: dict[str, tuple[str, ...]] = {
    "interview_qa": ("面试题", "问答", "q&a", "qa", "常见问题", "八股"),
    "concept_guide": ("是什么", "原理", "概念", "定义", "作用", "区别", "overview", "introduction"),
    "design_notes": ("设计", "架构", "trade-off", "权衡", "方案", "design", "architecture"),
    "project_review": ("项目", "复盘", "实践", "落地", "案例", "project", "postmortem"),
}

CONTENT_HINT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "question_answer": ("问：", "答：", "q:", "a:", "?"),
    "concept_explanation": ("是什么", "定义", "原理", "作用", "区别", "特性"),
    "design_discussion": ("架构", "设计", "权衡", "trade-off", "方案", "扩展性", "高可用"),
    "implementation_detail": ("实现", "代码", "接口", "流程", "步骤", "配置", "deployment"),
    "example_driven": ("例如", "比如", "案例", "实践", "示例", "场景"),
}


def classify_document_kind(file_name: str, sections: list[LoadedSection]) -> str:
    joined = " ".join(
        filter(
            None,
            [file_name, *[section.section_title or "" for section in sections], *[section.text[:400] for section in sections[:6]]],
        )
    ).lower()

    scores = {
        kind: sum(joined.count(keyword.lower()) for keyword in keywords)
        for kind, keywords in DOCUMENT_KIND_KEYWORDS.items()
    }

    if _looks_like_qa_document(sections):
        scores["interview_qa"] += 3

    best_kind, best_score = max(scores.items(), key=lambda item: item[1], default=("general", 0))
    return best_kind if best_score > 0 else "general"


def infer_chunk_content_type(text: str, section_title: str | None = None) -> str:
    normalized = " ".join(filter(None, [section_title or "", text])).lower()
    scores = {
        hint: sum(normalized.count(keyword.lower()) for keyword in keywords)
        for hint, keywords in CONTENT_HINT_KEYWORDS.items()
    }

    if _looks_like_question_answer_text(text):
        scores["question_answer"] += 2

    best_hint, best_score = max(scores.items(), key=lambda item: item[1], default=("general", 0))
    return best_hint if best_score > 0 else "general"


def starts_with_question(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    first_line = stripped.splitlines()[0].strip()
    return first_line.endswith("?") or first_line.endswith("？") or first_line.lower().startswith(("q:", "问："))


def _looks_like_question_answer_text(text: str) -> bool:
    normalized = text.lower()
    return any(token in normalized for token in ("问：", "答：", "q:", "a:"))


def _looks_like_qa_document(sections: list[LoadedSection]) -> bool:
    sample = "\n".join(section.text[:300] for section in sections[:5]).lower()
    qa_hits = len(re.findall(r"(问：|答：|q:|a:)", sample))
    return qa_hits >= 2
