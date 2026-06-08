from __future__ import annotations

import re

from app.rag.context_assembler import build_structured_context_bundle
from app.rag.query_router import classify_query_route
from app.schemas.qa import QAContextBlock, QAReference
from app.utils import get_rag_config


SECTION_TITLES = {
    "concept": ("定义", "为什么重要", "关键点"),
    "interview": ("直接回答", "展开说明", "面试表达建议"),
    "design": ("核心思路", "权衡点", "落地建议"),
    "implementation": ("实现思路", "关键步骤", "注意事项"),
    "general": ("回答", "补充说明", "相关要点"),
}


def build_grounded_answer(question: str, references: list[QAReference]) -> str:
    rag_config = get_rag_config()
    if not references:
        if not rag_config.answering.fallback_when_empty:
            return ""
        return (
            "⚠️ 当前知识库未检索到足够证据。\n\n"
            "据我所知，以下内容基于通用知识补充，仅供参考。\n\n"
            "RAG（Retrieval-Augmented Generation，检索增强生成）是一种先检索外部知识，再结合模型生成答案的方法。"
            "它的核心价值是让回答尽量建立在可追溯资料之上，从而减少幻觉，并提升时效性与专业性。"
        )

    _, context_blocks = build_structured_context_bundle(question, references)
    route = classify_query_route(question)
    titles = SECTION_TITLES.get(route.intent, SECTION_TITLES["general"])
    paragraphs = _build_paragraphs(context_blocks, limit=3)

    sections: list[str] = []
    for index, paragraph in enumerate(paragraphs):
        title = titles[index] if index < len(titles) else f"补充说明 {index + 1}"
        sections.append(f"### {title}\n{paragraph}")

    answer = "\n\n".join(sections).strip()
    if answer:
        return answer

    fallback_lines = _extract_supporting_lines(references, max_lines=3)
    if not fallback_lines:
        return "当前已检索到参考片段，但暂时无法整理出稳定答案。建议换一个更具体的问题再试一次。"
    return "\n".join(f"- {line}" for line in fallback_lines)


def _build_paragraphs(context_blocks: list[QAContextBlock], limit: int) -> list[str]:
    paragraphs: list[str] = []
    for block in context_blocks:
        lines = _extract_lines_from_block(block, max_lines=2)
        if not lines:
            continue
        paragraphs.append(" ".join(lines))
        if len(paragraphs) >= limit:
            break
    return paragraphs


def _extract_lines_from_block(block: QAContextBlock, max_lines: int) -> list[str]:
    lines: list[str] = []
    for reference in block.references:
        for line in _normalize_snippet_lines(reference.snippet):
            if line not in lines:
                lines.append(line)
            if len(lines) >= max_lines:
                return lines
    return lines


def _extract_supporting_lines(references: list[QAReference], max_lines: int) -> list[str]:
    lines: list[str] = []
    for reference in references:
        for line in _normalize_snippet_lines(reference.snippet):
            if line not in lines:
                lines.append(line)
            if len(lines) >= max_lines:
                return lines
    return lines


def _normalize_snippet_lines(snippet: str) -> list[str]:
    cleaned = snippet.replace("\r\n", "\n").replace("\r", "\n")
    raw_lines = [line.strip() for line in cleaned.splitlines()]
    normalized: list[str] = []
    for line in raw_lines:
        compact = re.sub(r"^[\-+*#\d\.\)\s]+", "", line).strip()
        compact = re.sub(r"\s+", " ", compact)
        if not compact:
            continue
        if len(compact) < 8:
            continue
        if compact in {"分工明确", "并行召回", "核心方案"}:
            continue
        normalized.append(compact)
    return normalized
