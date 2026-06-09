from dataclasses import dataclass


@dataclass
class LoadedSection:
    text: str
    section_title: str | None = None
    page_no: int | None = None
    section_level: int | None = None
    section_path: tuple[str, ...] = ()
