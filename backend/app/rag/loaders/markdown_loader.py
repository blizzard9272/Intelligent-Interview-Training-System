import re
from pathlib import Path

from app.rag.cleaners.text_cleaner import clean_text
from app.rag.types import LoadedSection

HEADER_PATTERN = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)


def load_markdown_file(file_path: str) -> list[LoadedSection]:
    content = Path(file_path).read_text(encoding="utf-8")
    matches = list(HEADER_PATTERN.finditer(content))
    if not matches:
        return [LoadedSection(text=clean_text(content))]

    sections: list[LoadedSection] = []
    preface = clean_text(content[: matches[0].start()])
    if preface:
        sections.append(LoadedSection(text=preface))

    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        body = clean_text(content[start:end])
        if not body:
            continue
        sections.append(LoadedSection(text=body, section_title=clean_text(match.group(2).strip())))
    return sections or [LoadedSection(text=clean_text(content))]
