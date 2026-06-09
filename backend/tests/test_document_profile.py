from __future__ import annotations

from pathlib import Path
import sys
import unittest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.rag.document_profile import classify_document_kind, infer_chunk_content_type, starts_with_question
from app.rag.types import LoadedSection


class DocumentProfileTests(unittest.TestCase):
    def test_classify_document_kind_detects_concept_guide(self) -> None:
        sections = [
            LoadedSection(
                section_title="什么是 RAG",
                text="RAG 的定义、原理、作用以及与微调的区别。它适合知识库问答场景。",
            )
        ]
        self.assertEqual(classify_document_kind("rag_overview.md", sections), "concept_guide")

    def test_classify_document_kind_detects_concept_guide_from_preface_and_filename(self) -> None:
        sections = [
            LoadedSection(
                text="RAG 的全称是 Retrieval-Augmented Generation，也就是检索增强生成。",
            ),
            LoadedSection(
                section_title="为什么需要RAG？",
                text="因为模型知识存在时效性限制，需要外部知识补充。",
            ),
        ]
        self.assertEqual(classify_document_kind("对RAG了解吗？谈谈什么是RAG？.md", sections), "concept_guide")

    def test_classify_document_kind_detects_interview_qa(self) -> None:
        sections = [
            LoadedSection(
                section_title="面试题",
                text="问：什么是依赖注入？答：依赖由外部传入。问：它的优点是什么？答：更利于测试。",
            )
        ]
        self.assertEqual(classify_document_kind("python_qa.md", sections), "interview_qa")

    def test_infer_chunk_content_type_detects_design_discussion(self) -> None:
        text = "系统设计时需要考虑架构分层、扩展性、故障隔离以及关键 trade-off。"
        self.assertEqual(infer_chunk_content_type(text, "系统设计"), "design_discussion")

    def test_infer_chunk_content_type_prefers_concept_for_definition_heading(self) -> None:
        text = "RAG 是一种通过先检索外部知识再生成答案的方法，常用于知识库问答。"
        self.assertEqual(infer_chunk_content_type(text, "什么是 RAG"), "concept_explanation")

    def test_starts_with_question_detects_question_opening(self) -> None:
        self.assertTrue(starts_with_question("什么是 RAG？它和搜索有什么区别？"))
        self.assertFalse(starts_with_question("RAG 是一种检索增强生成方法。"))
