from __future__ import annotations

import re

from app.rag.types import LoadedSection


DOCUMENT_KIND_KEYWORDS: dict[str, tuple[str, ...]] = {
    "interview_qa": ("面试题", "问答", "q&a", "qa", "常见问题", "八股", "高频题", "回答思路", "谈谈", "了解吗"),
    "concept_guide": ("是什么", "原理", "概念", "定义", "作用", "区别", "overview", "introduction", "why", "what", "全称", "检索增强生成"),
    "design_notes": ("设计", "架构", "trade-off", "权衡", "方案", "design", "architecture"),
    "project_review": ("项目", "复盘", "实践", "落地", "案例", "project", "postmortem", "故障", "优化"),
}

CONTENT_HINT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "question_answer": ("问：", "答：", "q:", "a:", "常见问题", "面试题"),
    "concept_explanation": ("是什么", "定义", "原理", "作用", "区别", "特性", "核心概念", "简介"),
    "design_discussion": ("架构", "设计", "权衡", "trade-off", "方案", "扩展性", "高可用", "一致性"),
    "implementation_detail": ("实现", "代码", "接口", "流程", "步骤", "配置", "deployment", "示例代码"),
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
        kind: _weighted_keyword_score(joined, keywords)
        for kind, keywords in DOCUMENT_KIND_KEYWORDS.items()
    }

    if _looks_like_qa_document(sections):
        scores["interview_qa"] += 3
    if _looks_like_concept_document(file_name, sections):
        scores["concept_guide"] += 3

    best_kind, best_score = max(scores.items(), key=lambda item: item[1], default=("general", 0))
    return best_kind if best_score > 0 else "general"


def infer_chunk_content_type(text: str, section_title: str | None = None) -> str:
    normalized = " ".join(filter(None, [section_title or "", text])).lower()
    scores = {
        hint: _weighted_keyword_score(normalized, keywords)
        for hint, keywords in CONTENT_HINT_KEYWORDS.items()
    }

    if _looks_like_question_answer_text(text):
        scores["question_answer"] += 3
    if starts_with_question(text):
        scores["question_answer"] += 2
        scores["concept_explanation"] += 1
    if _looks_like_definition_title(section_title):
        scores["concept_explanation"] += 2
    if _looks_like_implementation_title(section_title):
        scores["implementation_detail"] += 2
    if _looks_like_design_title(section_title):
        scores["design_discussion"] += 2
    if _looks_like_example_title(section_title):
        scores["example_driven"] += 2

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


def _looks_like_concept_document(file_name: str, sections: list[LoadedSection]) -> bool:
    normalized_name = file_name.lower()
    if any(token in normalized_name for token in ("什么是", "了解吗", "谈谈", "overview", "introduction")):
        return True
    sample = " ".join(
        filter(
            None,
            [section.section_title or "" for section in sections[:4]] + [section.text[:200] for section in sections[:3]],
        )
    ).lower()
    concept_hits = sum(
        sample.count(token)
        for token in ("什么是", "定义", "原理", "为什么需要", "全称", "检索增强生成")
    )
    return concept_hits >= 2


def _looks_like_definition_title(section_title: str | None) -> bool:
    if not section_title:
        return False
    normalized = section_title.strip().lower()
    return any(token in normalized for token in ("什么是", "定义", "原理", "概念", "介绍", "简介"))


def _looks_like_implementation_title(section_title: str | None) -> bool:
    if not section_title:
        return False
    normalized = section_title.strip().lower()
    return any(token in normalized for token in ("实现", "流程", "步骤", "代码", "配置", "落地"))


def _looks_like_design_title(section_title: str | None) -> bool:
    if not section_title:
        return False
    normalized = section_title.strip().lower()
    return any(token in normalized for token in ("架构", "设计", "方案", "权衡", "trade-off"))


def _looks_like_example_title(section_title: str | None) -> bool:
    if not section_title:
        return False
    normalized = section_title.strip().lower()
    return any(token in normalized for token in ("示例", "案例", "实践", "场景", "例如"))


def _weighted_keyword_score(text: str, keywords: tuple[str, ...]) -> int:
    score = 0
    for keyword in keywords:
        lowered = keyword.lower()
        hits = text.count(lowered)
        if hits <= 0:
            continue
        score += hits * (2 if len(lowered) >= 4 else 1)
    return score
