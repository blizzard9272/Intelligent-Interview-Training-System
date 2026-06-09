import re

from app.rag.document_profile import infer_chunk_content_type, starts_with_question
from app.rag.types import LoadedSection
from app.utils import get_rag_config


def split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = max(end - chunk_overlap, 0)
    return chunks


def build_chunks(sections: list[LoadedSection]) -> list[dict]:
    chunking_config = get_rag_config().chunking
    chunks: list[dict] = []
    for section_index, section in enumerate(sections):
        section_chunks = _build_section_chunks(
            section,
            chunk_size=chunking_config.chunk_size,
            chunk_overlap=chunking_config.chunk_overlap,
        )
        for chunk_index, chunk_text in enumerate(section_chunks):
            chunks.append(
                {
                    "text": chunk_text,
                    "section_title": section.section_title,
                    "page_no": section.page_no,
                    "section_index": section_index,
                    "chunk_index": chunk_index,
                    "section_level": section.section_level,
                    "section_path": list(section.section_path),
                    "content_type_hint": infer_chunk_content_type(chunk_text, section.section_title),
                    "starts_with_question": starts_with_question(chunk_text),
                }
            )
    return chunks


def _build_section_chunks(section: LoadedSection, *, chunk_size: int, chunk_overlap: int) -> list[str]:
    body = section.text.strip()
    if not body:
        return []

    heading_prefix = _build_heading_prefix(section)
    available_body_size = max(120, chunk_size - len(heading_prefix))
    paragraphs = _split_into_paragraphs(body)
    if not paragraphs:
        return _format_chunks(
            split_text(body, available_body_size, min(chunk_overlap, max(0, available_body_size // 4))),
            heading_prefix,
        )

    chunks: list[str] = []
    current_parts: list[str] = []
    current_length = 0

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        if len(paragraph) > available_body_size:
            if current_parts:
                chunks.append(heading_prefix + "\n\n".join(current_parts))
                current_parts = []
                current_length = 0
            chunks.extend(
                _format_chunks(
                    split_text(
                        paragraph,
                        available_body_size,
                        min(chunk_overlap, max(0, available_body_size // 4)),
                    ),
                    heading_prefix,
                )
            )
            continue

        next_length = current_length + len(paragraph) + (2 if current_parts else 0)
        if current_parts and next_length > available_body_size:
            chunks.append(heading_prefix + "\n\n".join(current_parts))
            current_parts = [paragraph]
            current_length = len(paragraph)
            continue

        current_parts.append(paragraph)
        current_length = next_length

    if current_parts:
        chunks.append(heading_prefix + "\n\n".join(current_parts))

    return chunks


def _build_heading_prefix(section: LoadedSection) -> str:
    if section.section_path:
        return f"标题路径：{' > '.join(section.section_path)}\n\n"
    if section.section_title:
        return f"标题：{section.section_title}\n\n"
    return ""


def _split_into_paragraphs(text: str) -> list[str]:
    if "\n\n" in text:
        parts = [item.strip() for item in re.split(r"\n{2,}", text) if item.strip()]
    else:
        parts = _merge_short_lines(text)
    return _merge_list_blocks(parts)


def _merge_short_lines(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return []

    merged: list[str] = []
    buffer: list[str] = []
    for line in lines:
        is_list_like = line.startswith(("- ", "* ", "+ ")) or bool(re.match(r"^\d+\.\s+", line))
        if is_list_like:
            if buffer:
                merged.append(" ".join(buffer))
                buffer = []
            merged.append(line)
            continue

        buffer.append(line)
        if len(" ".join(buffer)) >= 140 or line.endswith(("。", "！", "？", ".", ":", "：")):
            merged.append(" ".join(buffer))
            buffer = []

    if buffer:
        merged.append(" ".join(buffer))
    return merged


def _merge_list_blocks(parts: list[str]) -> list[str]:
    merged: list[str] = []
    list_buffer: list[str] = []
    for part in parts:
        is_list_like = all(
            line.startswith(("- ", "* ", "+ ")) or bool(re.match(r"^\d+\.\s+", line))
            for line in part.splitlines()
            if line.strip()
        )
        if is_list_like:
            list_buffer.append(part)
            continue
        if list_buffer:
            merged.append("\n".join(list_buffer))
            list_buffer = []
        merged.append(part)

    if list_buffer:
        merged.append("\n".join(list_buffer))
    return merged


def _format_chunks(parts: list[str], heading_prefix: str) -> list[str]:
    return [heading_prefix + item.strip() for item in parts if item.strip()]
