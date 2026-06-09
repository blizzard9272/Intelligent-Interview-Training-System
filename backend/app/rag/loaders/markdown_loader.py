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

    heading_stack: list[str] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        body = clean_text(content[start:end])
        if not body:
            continue
        level = len(match.group(1))
        title = clean_text(match.group(2).strip())
        if not title:
            continue

        heading_stack = heading_stack[: level - 1]
        heading_stack.append(title)
        sections.append(
            LoadedSection(
                text=body,
                section_title=title,
                section_level=level,
                section_path=tuple(heading_stack),
            )
        )
    return sections or [LoadedSection(text=clean_text(content))]
