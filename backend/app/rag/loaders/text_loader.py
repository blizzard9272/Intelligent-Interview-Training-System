from pathlib import Path

from app.rag.cleaners.text_cleaner import clean_text
from app.rag.types import LoadedSection


def load_text_file(file_path: str) -> list[LoadedSection]:
    text = Path(file_path).read_text(encoding="utf-8")
    return [LoadedSection(text=clean_text(text))]
