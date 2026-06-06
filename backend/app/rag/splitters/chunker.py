"""
负责对文本进行分块处理，将长文本切分成适合模型处理的小块。主要功能包括：
1. 文本分块：根据配置的chunk_size和chunk_overlap参数，将输入文本切分成多个重叠的小块，确保每个块的长度不超过chunk_size
2. 块信息构建：为每个文本块构建包含文本内容、所属章节标题、页码、章节索引和块索引等信息的字典，方便后续处理和存储。
3. 配置支持：通过get_rag_config函数获取分块相关的配置参数，确保分块过程的灵活性和可调整性。
4. 适用范围：适用于需要将长文本输入模型进行处理的场景，如文档问答、知识库构建等，帮助提升模型的处理效率和效果。
"""
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
                }
            )
    return chunks
