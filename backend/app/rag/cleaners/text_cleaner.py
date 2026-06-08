"""
分则文本清洗、换行与空白规范化等功能，确保输入文本的一致性和可读性。
"""
import html
import re


def clean_text(text: str) -> str:
    if not text:
        return ""

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = html.unescape(normalized)
    normalized = normalized.replace("\u00a0", " ")
    normalized = normalized.replace("\u200b", "")
    normalized = re.sub(r"<[^>\n]+>", "", normalized)
    normalized = re.sub(r'[\w#(),.;:%\-/\s]*">', "", normalized)
    normalized = re.sub(r"<[^>\n]*", "", normalized)
    normalized = re.sub(r"\*\*", "", normalized)
    normalized = re.sub(r"__[ \t]*", "", normalized)
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r" *\n *", "\n", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()
