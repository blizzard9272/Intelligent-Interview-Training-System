import fitz

from app.rag.cleaners.text_cleaner import clean_text
from app.rag.types import LoadedSection


def load_pdf_file(file_path: str) -> list[LoadedSection]:
    sections: list[LoadedSection] = []
    document = fitz.open(file_path)
    try:
        for page_index, page in enumerate(document, start=1):
            text = clean_text(page.get_text("text"))
            if not text:
                continue
            sections.append(LoadedSection(text=text, page_no=page_index))
    finally:
        document.close()
    return sections
