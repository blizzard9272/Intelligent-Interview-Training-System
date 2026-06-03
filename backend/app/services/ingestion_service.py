from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models.document import Document
from app.db.models.ingestion_task import IngestionTask
from app.rag.embeddings.hash_embedding import HashEmbeddingProvider
from app.rag.loaders.factory import load_sections
from app.rag.splitters.chunker import build_chunks
from app.rag.vector_store import ChromaVectorStore


class IngestionService:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_provider = HashEmbeddingProvider()
        self.vector_store = ChromaVectorStore()

    def process_document(self, document_id: int, task_id: int) -> None:
        document = self.db.get(Document, document_id)
        task = self.db.get(IngestionTask, task_id)
        if not document or not task:
            return

        try:
            self._mark_started(document, task)
            sections = load_sections(document.file_path, document.file_type)
            self._update_task(task, progress=25, message="Loaded and cleaned source content")

            chunks = build_chunks(sections)
            if not chunks:
                raise ValueError("No content extracted from document")

            self._update_task(task, progress=50, message="Generated chunks")

            texts = [chunk["text"] for chunk in chunks]
            embeddings = self.embedding_provider.embed_documents(texts)
            self._update_task(task, progress=75, message="Computed embeddings")

            ids: list[str] = []
            metadatas: list[dict] = []
            for index, chunk in enumerate(chunks):
                ids.append(f"doc-{document.id}-chunk-{index}")
                metadatas.append(
                    {
                        "user_id": document.user_id,
                        "knowledge_base_id": document.knowledge_base_id,
                        "document_id": document.id,
                        "file_name": document.file_name,
                        "file_type": document.file_type,
                        "chunk_index": index,
                        "section_title": chunk["section_title"] or "",
                        "page_no": chunk["page_no"] or 0,
                    }
                )

            self.vector_store.delete_document_chunks(document.id)
            self.vector_store.add_chunks(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)

            document.status = "completed"
            document.chunk_count = len(chunks)
            document.parse_error = None
            task.status = "completed"
            task.progress = 100
            task.message = "Vector ingestion completed"
            task.finished_at = datetime.now(timezone.utc)
            self.db.commit()
        except Exception as exc:
            document.status = "failed"
            document.parse_error = str(exc)
            task.status = "failed"
            task.message = str(exc)
            task.finished_at = datetime.now(timezone.utc)
            self.db.commit()
            raise

    def _mark_started(self, document: Document, task: IngestionTask) -> None:
        document.status = "processing"
        document.parse_error = None
        task.status = "running"
        task.progress = 10
        task.message = "Starting ingestion"
        task.started_at = datetime.now(timezone.utc)
        self.db.commit()

    def _update_task(self, task: IngestionTask, progress: int, message: str) -> None:
        task.progress = progress
        task.message = message
        self.db.commit()
