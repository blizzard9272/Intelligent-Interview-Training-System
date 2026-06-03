from app.rag.loaders.markdown_loader import load_markdown_file
from app.rag.loaders.pdf_loader import load_pdf_file
from app.rag.loaders.text_loader import load_text_file
from app.rag.types import LoadedSection


def load_sections(file_path: str, file_type: str) -> list[LoadedSection]:
    normalized = file_type.lower()
    if normalized == "txt":
        return load_text_file(file_path)
    if normalized == "md":
        return load_markdown_file(file_path)
    if normalized == "pdf":
        return load_pdf_file(file_path)
    raise ValueError(f"Unsupported file type: {file_type}")
