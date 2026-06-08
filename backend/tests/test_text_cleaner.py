from __future__ import annotations

import unittest

from app.rag.cleaners.text_cleaner import clean_text


class TextCleanerTests(unittest.TestCase):
    def test_clean_text_removes_html_tags_and_entities(self) -> None:
        raw = '<font style="color:red">什么是 RAG？</font>&nbsp;<b>它用于检索增强生成。</b>'

        cleaned = clean_text(raw)

        self.assertEqual(cleaned, "什么是 RAG？ 它用于检索增强生成。")

    def test_clean_text_removes_broken_rich_text_fragments(self) -> None:
        raw = '1);">短期记忆是挥发的。\n<font style="color:rgb(15, 17, 21);">长期记忆可按相关性检索。</font>'

        cleaned = clean_text(raw)

        self.assertEqual(cleaned, "短期记忆是挥发的。\n长期记忆可按相关性检索。")


if __name__ == "__main__":
    unittest.main()
