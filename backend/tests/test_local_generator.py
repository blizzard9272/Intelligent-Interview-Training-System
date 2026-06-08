from __future__ import annotations

from types import SimpleNamespace
import unittest
from unittest.mock import patch

from app.rag.generators.local_generator import build_grounded_answer
from app.schemas.qa import QAReference


class LocalGeneratorTests(unittest.TestCase):
    def test_build_grounded_answer_returns_user_facing_text(self) -> None:
        references = [
            QAReference(
                document_id=1,
                file_name="rag.md",
                chunk_index=0,
                snippet="RAG 是一种先检索外部知识，再结合模型生成答案的方法。\n它的目标是减少幻觉并提升可追溯性。",
                content_type_hint="concept_explanation",
                context_role="concept",
            ),
            QAReference(
                document_id=2,
                file_name="rag.md",
                chunk_index=1,
                snippet="它适用于知识更新频繁、需要引用企业文档或专业资料的问答场景。",
                content_type_hint="example_driven",
                context_role="example",
            ),
        ]
        rag_config = SimpleNamespace(answering=SimpleNamespace(fallback_when_empty=True))

        with patch("app.rag.generators.local_generator.get_rag_config", return_value=rag_config):
            answer = build_grounded_answer("什么是RAG？", references)

        self.assertIn("### 定义", answer)
        self.assertNotIn("System guidance", answer)
        self.assertNotIn("Structured retrieved context", answer)
        self.assertIn("RAG 是一种先检索外部知识", answer)


if __name__ == "__main__":
    unittest.main()
