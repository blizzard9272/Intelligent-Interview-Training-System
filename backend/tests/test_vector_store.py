from __future__ import annotations

import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
import app.db.models  # noqa: F401
from app.db.models.document import Document
from app.db.models.knowledge_base import KnowledgeBase
from app.db.models.user import User
from app.rag.vector_store import PGVectorStore


class PGVectorStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine, autoflush=False, autocommit=False, class_=Session)
        self.db = self.session_factory()

        self.user = User(username="vector-user", email="vector-user@example.com", password_hash="hashed")
        self.db.add(self.user)
        self.db.commit()
        self.db.refresh(self.user)

        self.knowledge_base = KnowledgeBase(user_id=self.user.id, name="Vector KB")
        self.db.add(self.knowledge_base)
        self.db.commit()
        self.db.refresh(self.knowledge_base)

        self.document = Document(
            user_id=self.user.id,
            knowledge_base_id=self.knowledge_base.id,
            file_name="rag.md",
            file_type="md",
            file_path="storage/uploads/rag.md",
            file_size=128,
            status="completed",
            chunk_count=2,
            document_kind="concept_guide",
        )
        self.db.add(self.document)
        self.db.commit()
        self.db.refresh(self.document)

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def test_add_query_get_and_delete_chunks(self) -> None:
        store = PGVectorStore(self.db)
        store.add_chunks(
            ids=["doc-1-chunk-0", "doc-1-chunk-1"],
            documents=[
                "RAG 是一种结合检索和生成的方案。",
                "微调修改参数，RAG 侧重外部知识检索。",
            ],
            embeddings=[
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
            ],
            metadatas=[
                {
                    "user_id": self.user.id,
                    "knowledge_base_id": self.knowledge_base.id,
                    "document_id": self.document.id,
                    "file_name": "rag.md",
                    "file_type": "md",
                    "document_kind": "concept_guide",
                    "chunk_index": 0,
                    "section_title": "RAG 定义",
                    "page_no": 0,
                    "section_index": 0,
                    "content_type_hint": "concept_explanation",
                    "starts_with_question": False,
                },
                {
                    "user_id": self.user.id,
                    "knowledge_base_id": self.knowledge_base.id,
                    "document_id": self.document.id,
                    "file_name": "rag.md",
                    "file_type": "md",
                    "document_kind": "concept_guide",
                    "chunk_index": 1,
                    "section_title": "RAG 对比",
                    "page_no": 0,
                    "section_index": 1,
                    "content_type_hint": "concept_explanation",
                    "starts_with_question": False,
                },
            ],
        )

        query_result = store.query(
            query_embedding=[0.9, 0.1, 0.0],
            user_id=self.user.id,
            knowledge_base_id=self.knowledge_base.id,
            top_k=2,
            extra_filters=[{"content_type_hint": "concept_explanation"}],
        )
        self.assertEqual(len(query_result["documents"][0]), 2)
        self.assertIn("RAG 是一种结合检索和生成的方案。", query_result["documents"][0][0])

        chunk_result = store.get_document_chunks(user_id=self.user.id, document_id=self.document.id)
        self.assertEqual(len(chunk_result["documents"]), 2)
        self.assertEqual(chunk_result["metadatas"][0]["section_title"], "RAG 定义")

        store.delete_document_chunks(self.document.id)
        deleted_result = store.get_document_chunks(user_id=self.user.id, document_id=self.document.id)
        self.assertEqual(deleted_result["documents"], [])


if __name__ == "__main__":
    unittest.main()
