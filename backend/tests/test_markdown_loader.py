from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from app.rag.loaders.markdown_loader import load_markdown_file


class MarkdownLoaderTests(unittest.TestCase):
    def test_load_markdown_file_keeps_preface_before_first_heading(self) -> None:
        content = (
            "RAG 的全称是 Retrieval-Augmented Generation。\n"
            "它会先检索资料，再生成回答。\n\n"
            "## 为什么需要RAG？\n"
            "因为模型知识有时效性和领域覆盖限制。\n"
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "rag.md"
            file_path.write_text(content, encoding="utf-8")

            sections = load_markdown_file(str(file_path))

        self.assertEqual(len(sections), 2)
        self.assertIsNone(sections[0].section_title)
        self.assertIn("RAG 的全称", sections[0].text)
        self.assertEqual(sections[1].section_title, "为什么需要RAG？")


if __name__ == "__main__":
    unittest.main()
