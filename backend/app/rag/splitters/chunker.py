from app.core.config import settings
from app.rag.types import LoadedSection


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
    chunks: list[dict] = []
    for section_index, section in enumerate(sections):
        for chunk_index, chunk_text in enumerate(
            split_text(section.text, settings.chunk_size, settings.chunk_overlap)
        ):
            chunks.append(
                {
                    "text": chunk_text,
                    "section_title": section.section_title,
                    "page_no": section.page_no,
                    "section_index": section_index,
                    "chunk_index": chunk_index,
                }
            )
    return chunks
