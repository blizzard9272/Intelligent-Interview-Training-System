from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.rag.splitters.chunker import build_chunks
from app.rag.types import LoadedSection


class ChunkerTests(unittest.TestCase):
    def test_build_chunks_prefixes_heading_path_for_markdown_sections(self) -> None:
        rag_config = SimpleNamespace(
            chunking=SimpleNamespace(
                chunk_size=500,
                chunk_overlap=80,
            )
        )
        sections = [
            LoadedSection(
                text="RAG 会先检索相关资料，再结合上下文生成回答。",
                section_title="什么是 RAG",
                section_level=2,
                section_path=("RAG", "什么是 RAG"),
            )
        ]

        with patch("app.rag.splitters.chunker.get_rag_config", return_value=rag_config):
            chunks = build_chunks(sections)

        self.assertEqual(len(chunks), 1)
        self.assertIn("标题路径：RAG > 什么是 RAG", chunks[0]["text"])
        self.assertEqual(chunks[0]["section_path"], ["RAG", "什么是 RAG"])

    def test_build_chunks_uses_paragraph_boundaries_before_fallback_windowing(self) -> None:
        rag_config = SimpleNamespace(
            chunking=SimpleNamespace(
                chunk_size=150,
                chunk_overlap=40,
            )
        )
        sections = [
            LoadedSection(
                text=(
                    "第一段解释 RAG 的基本定义，以及它为何适合知识库问答场景，还补充说明了外部知识接入、事实约束和答案可追溯性的价值。\n\n"
                    "第二段说明检索和生成如何协同工作，并强调标题结构对于召回的重要性，同时提到段落边界、语义焦点和引用片段的完整性。\n\n"
                    "第三段补充一个例子，展示标题语义能如何帮助模型锁定正确上下文，并避免把不同主题的内容错误拼接在一起。"
                ),
                section_title="RAG 基础",
                section_level=2,
                section_path=("RAG", "RAG 基础"),
            )
        ]

        with patch("app.rag.splitters.chunker.get_rag_config", return_value=rag_config):
            chunks = build_chunks(sections)

        self.assertGreaterEqual(len(chunks), 2)
        self.assertTrue(any("第一段解释 RAG" in item["text"] for item in chunks))
        self.assertTrue(any("第二段说明检索和生成" in item["text"] for item in chunks))
        self.assertFalse(any("基础。\n\n第二段" in item["text"] for item in chunks))


if __name__ == "__main__":
    unittest.main()
