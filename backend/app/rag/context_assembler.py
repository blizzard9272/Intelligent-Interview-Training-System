from __future__ import annotations

from collections import defaultdict

from app.rag.query_router import classify_query_route
from app.schemas.qa import QAContextBlock, QAReference


ROLE_LABELS = {
    "core_answer": "核心回答",
    "concept": "概念与原理",
    "design": "设计与权衡",
    "implementation": "实现细节",
    "example": "示例与场景",
    "qa_pair": "问答材料",
    "general": "补充上下文",
}

ROLE_ORDER_BY_INTENT = {
    "concept": ("core_answer", "concept", "qa_pair", "example", "implementation", "design", "general"),
    "interview": ("core_answer", "qa_pair", "concept", "example", "implementation", "design", "general"),
    "design": ("core_answer", "design", "example", "concept", "implementation", "qa_pair", "general"),
    "implementation": ("core_answer", "implementation", "example", "concept", "design", "qa_pair", "general"),
    "general": ("core_answer", "concept", "example", "implementation", "design", "qa_pair", "general"),
}


def build_structured_context(question: str, references: list[QAReference]) -> str:
    context_text, _ = build_structured_context_bundle(question, references)
    return context_text


def build_structured_context_bundle(question: str, references: list[QAReference]) -> tuple[str, list[QAContextBlock]]:
    if not references:
        return "当前没有可用的检索上下文。", []

    route = classify_query_route(question)
    grouped: dict[str, list[QAReference]] = defaultdict(list)
    for reference in references:
        role = reference.context_role or infer_context_role(reference)
        grouped[role].append(reference)

    ordered_roles = ROLE_ORDER_BY_INTENT.get(route.intent, ROLE_ORDER_BY_INTENT["general"])
    blocks: list[str] = []
    context_blocks: list[QAContextBlock] = []
    used_roles: set[str] = set()

    for role in ordered_roles:
        items = grouped.get(role)
        if not items:
            continue
        used_roles.add(role)
        blocks.append(_render_block(role, items))
        context_blocks.append(_build_context_block(role, items))

    for role, items in grouped.items():
        if role in used_roles:
            continue
        blocks.append(_render_block(role, items))
        context_blocks.append(_build_context_block(role, items))

    return "\n\n".join(blocks), context_blocks


def infer_context_role(reference: QAReference) -> str:
    content_type = (reference.content_type_hint or "").strip().lower()
    if content_type == "concept_explanation":
        return "concept"
    if content_type == "design_discussion":
        return "design"
    if content_type == "implementation_detail":
        return "implementation"
    if content_type == "example_driven":
        return "example"
    if content_type == "question_answer":
        return "qa_pair"
    return "general"


def _render_block(role: str, references: list[QAReference]) -> str:
    label = ROLE_LABELS.get(role, role)
    lines = [f"## {label}"]
    for index, reference in enumerate(references, start=1):
        meta_parts = [f"文件={reference.file_name}", f"分块={reference.chunk_index}"]
        if reference.section_title:
            meta_parts.append(f"章节={reference.section_title}")
        lines.append(f"[{index}] {' | '.join(meta_parts)}")
        lines.append(reference.snippet.strip())
    return "\n".join(lines)


def _build_context_block(role: str, references: list[QAReference]) -> QAContextBlock:
    return QAContextBlock(role=role, title=ROLE_LABELS.get(role, role), references=references)
