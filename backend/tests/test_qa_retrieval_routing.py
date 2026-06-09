from __future__ import annotations

from types import SimpleNamespace
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
import app.db.models  # noqa: F401
from app.db.models.knowledge_base import KnowledgeBase
from app.db.models.user import User
from app.services.qa_service import QAService


class FakeEmbeddingProvider:
    def embed_query(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]


class FakeVectorStore:
    def __init__(self) -> None:
        self.calls: list[list[dict[str, object]] | None] = []

    def query(
        self,
        *,
        query_embedding: list[float],
        user_id: int,
        knowledge_base_id: int,
        top_k: int | None = None,
        extra_filters: list[dict[str, object]] | None = None,
    ) -> dict:
        self.calls.append(extra_filters)
        current_filter = extra_filters[0] if extra_filters else {}

        if current_filter == {"content_type_hint": "concept_explanation"}:
            return {
                "documents": [["RAG 的全称是 Retrieval-Augmented Generation。RAG 是一种结合检索与生成的方式。"]],
                "metadatas": [[{"document_id": 1, "file_name": "rag.md", "chunk_index": 0, "content_type_hint": "concept_explanation", "document_kind": "concept_guide", "section_title": "什么是RAG", "starts_with_question": False}]],
                "distances": [[0.42]],
            }
        if current_filter == {"content_type_hint": "question_answer"}:
            return {
                "documents": [["问：什么是 RAG？答：它通过检索增强回答。"]],
                "metadatas": [[{"document_id": 2, "file_name": "qa.md", "chunk_index": 0, "content_type_hint": "question_answer", "document_kind": "interview_qa", "section_title": "常见面试题", "starts_with_question": True}]],
                "distances": [[0.18]],
            }
        if current_filter == {"document_kind": "concept_guide"}:
            return {
                "documents": [["RAG 通常用于知识库问答。"]],
                "metadatas": [[{"document_id": 3, "file_name": "guide.md", "chunk_index": 1, "content_type_hint": "concept_explanation", "document_kind": "concept_guide", "section_title": "应用场景", "starts_with_question": False}]],
                "distances": [[0.51]],
            }
        if current_filter == {"document_kind": "interview_qa"}:
            return {
                "documents": [["问：RAG 和微调有什么区别？"]],
                "metadatas": [[{"document_id": 2, "file_name": "qa.md", "chunk_index": 0, "content_type_hint": "question_answer", "document_kind": "interview_qa", "section_title": "常见面试题", "starts_with_question": True}]],
                "distances": [[0.14]],
            }
        return {
            "documents": [["补充资料：微调修改参数，RAG 侧重外部知识检索。"]],
            "metadatas": [[{"document_id": 4, "file_name": "extra.md", "chunk_index": 2, "content_type_hint": "general", "document_kind": "general", "section_title": "补充说明", "starts_with_question": False}]],
            "distances": [[0.67]],
        }


class QAServiceRetrievalRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine, autoflush=False, autocommit=False, class_=Session)
        self.db = self.session_factory()

        self.user = User(username="route-user", email="route-user@example.com", password_hash="hashed")
        self.db.add(self.user)
        self.db.commit()
        self.db.refresh(self.user)

        self.knowledge_base = KnowledgeBase(user_id=self.user.id, name="Routing KB")
        self.db.add(self.knowledge_base)
        self.db.commit()
        self.db.refresh(self.knowledge_base)

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def test_retrieve_references_uses_routed_plan_and_fallback(self) -> None:
        service = QAService(self.db)
        fake_store = FakeVectorStore()
        service.embedding_provider = FakeEmbeddingProvider()
        service.vector_store = fake_store
        rag_config = SimpleNamespace(
            retrieval=SimpleNamespace(top_k=4, enable_rerank=False),
            answering=SimpleNamespace(max_reference_snippet_length=300),
        )

        with patch("app.services.qa_service.get_rag_config", return_value=rag_config):
            references = service.retrieve_references_for_question(
                user_id=self.user.id,
                knowledge_base_id=self.knowledge_base.id,
                question="什么是 RAG？它和微调有什么区别？",
            )

        self.assertEqual(
            fake_store.calls,
            [
                [{"content_type_hint": "concept_explanation"}],
                [{"content_type_hint": "question_answer"}],
                [{"document_kind": "concept_guide"}],
                [{"document_kind": "interview_qa"}],
                None,
            ],
        )
        self.assertEqual(len(references), 4)
        self.assertEqual(references[0].file_name, "rag.md")
        self.assertEqual(references[1].file_name, "qa.md")
        self.assertEqual(references[2].file_name, "guide.md")
        self.assertEqual(references[3].file_name, "extra.md")

    def test_retrieve_references_reranks_candidates_by_metadata_match(self) -> None:
        service = QAService(self.db)
        fake_store = FakeVectorStore()
        service.embedding_provider = FakeEmbeddingProvider()
        service.vector_store = fake_store
        rag_config = SimpleNamespace(
            retrieval=SimpleNamespace(top_k=4, enable_rerank=True),
            answering=SimpleNamespace(max_reference_snippet_length=300),
        )

        with patch("app.services.qa_service.get_rag_config", return_value=rag_config):
            references = service.retrieve_references_for_question(
                user_id=self.user.id,
                knowledge_base_id=self.knowledge_base.id,
                question="什么是 RAG？它和微调有什么区别？",
            )

        self.assertEqual(references[0].file_name, "rag.md")
        self.assertEqual(references[1].file_name, "guide.md")
        self.assertEqual(references[2].file_name, "qa.md")
        self.assertEqual(references[3].file_name, "extra.md")
        self.assertEqual(len(service._last_retrieval_steps), 5)
        self.assertEqual(service._last_retrieval_steps[0].filters, {"content_type_hint": "concept_explanation"})
        self.assertEqual(service._last_reranked_candidates[0].file_name, "rag.md")

        debug_trace = service._build_debug_trace(
            question="什么是 RAG？它和微调有什么区别？",
            references=references,
        )
        self.assertEqual(debug_trace.route_intent, "concept")
        self.assertEqual(len(debug_trace.retrieval_steps), 5)
        self.assertIn("## 核心回答", debug_trace.structured_context)

    def test_collect_candidates_builds_sentence_aware_snippet(self) -> None:
        service = QAService(self.db)
        long_doc = "第一句解释定义。第二句继续补充。第三句还在展开。第四句用于验证截断不要落在半句话中。"
        result = {
            "documents": [[long_doc]],
            "metadatas": [[{"document_id": 1, "file_name": "rag.md", "chunk_index": 0, "content_type_hint": "concept_explanation", "document_kind": "concept_guide", "section_title": "什么是RAG", "starts_with_question": False}]],
            "distances": [[0.1]],
        }
        candidates = service._collect_candidates_from_result(
            result=result,
            max_snippet_length=25,
            seen_chunks=set(),
            plan_filters={},
        )
        self.assertEqual(len(candidates), 1)
        snippet = candidates[0]["reference"].snippet
        self.assertNotEqual(snippet[-1], "开")
        self.assertNotEqual(snippet[-1], "展")
        self.assertLess(len(snippet), len(long_doc))


if __name__ == "__main__":
    unittest.main()
