from __future__ import annotations

import unittest

from app.db.models.document import Document
from app.db.models.ingestion_task import IngestionTask
from app.db.models.knowledge_base import KnowledgeBase
from app.db.session import SessionLocal
from app.rag.vector_store import PGVectorStore


class InspectRAGStateTests(unittest.TestCase):
    def test_print_current_rag_state(self) -> None:
        db = SessionLocal()
        try:
            print("=== Knowledge Bases ===")
            for kb in db.query(KnowledgeBase).order_by(KnowledgeBase.id.desc()).limit(10):
                print(f"id={kb.id} name={kb.name} user_id={kb.user_id}")

            print("=== Documents ===")
            for doc in db.query(Document).order_by(Document.id.desc()).limit(20):
                print(
                    f"id={doc.id} kb={doc.knowledge_base_id} name={doc.file_name} "
                    f"status={doc.status} chunks={doc.chunk_count} kind={doc.document_kind} "
                    f"error={doc.parse_error!r}"
                )

            print("=== Ingestion Tasks ===")
            for task in db.query(IngestionTask).order_by(IngestionTask.id.desc()).limit(20):
                print(
                    f"id={task.id} doc={task.document_id} status={task.status} "
                    f"progress={task.progress} message={task.message!r}"
                )
        finally:
            db.close()

        store = PGVectorStore()
        metadatas = store.list_chunk_metadatas(limit=10)
        total_chunks = store.count_chunks()
        print("=== PGVector Chunks ===")
        print(f"total_chunks={total_chunks}")
        for metadata in reversed(metadatas):
            print(metadata)

        self.assertGreaterEqual(total_chunks, 0)


if __name__ == "__main__":
    unittest.main()
