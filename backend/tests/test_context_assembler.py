from __future__ import annotations

import unittest

from app.rag.context_assembler import build_structured_context
from app.schemas.qa import QAReference


class ContextAssemblerTests(unittest.TestCase):
    def test_build_structured_context_groups_by_role_for_concept_question(self) -> None:
        references = [
            QAReference(
                document_id=1,
                file_name="qa.md",
                chunk_index=0,
                snippet="问：什么是 RAG？答：它结合检索与生成。",
                content_type_hint="question_answer",
                context_role="core_answer",
            ),
            QAReference(
                document_id=2,
                file_name="guide.md",
                chunk_index=1,
                snippet="RAG 的核心是先检索外部知识，再组织回答。",
                content_type_hint="concept_explanation",
                section_title="基本原理",
                context_role="concept",
            ),
            QAReference(
                document_id=3,
                file_name="example.md",
                chunk_index=2,
                snippet="例如在知识库问答中，RAG 可以减少幻觉。",
                content_type_hint="example_driven",
                context_role="example",
            ),
        ]

        context = build_structured_context("什么是 RAG？它和微调有什么区别？", references)

        self.assertIn("## 核心回答", context)
        self.assertIn("## 概念与原理", context)
        self.assertIn("## 示例与场景", context)
        self.assertLess(context.index("## 核心回答"), context.index("## 概念与原理"))
        self.assertLess(context.index("## 概念与原理"), context.index("## 示例与场景"))


if __name__ == "__main__":
    unittest.main()
