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
        for chunk_index, chunk_text in enumerate(
            split_text(section.text, chunking_config.chunk_size, chunking_config.chunk_overlap)
        ):
            chunks.append(
                {
                    "text": chunk_text,
                    "section_title": section.section_title,
                    "page_no": section.page_no,
                    "section_index": section_index,
                    "chunk_index": chunk_index,
                    "content_type_hint": infer_chunk_content_type(chunk_text, section.section_title),
                    "starts_with_question": starts_with_question(chunk_text),
                }
            )
    return chunks
