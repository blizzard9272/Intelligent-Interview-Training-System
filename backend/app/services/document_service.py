from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.document import Document
from app.rag.vector_store import ChromaVectorStore


class DocumentService:
    def __init__(self, db: Session):
        self.db = db

    def list_by_user(self, user_id: int, knowledge_base_id: int | None = None) -> list[Document]:
        stmt = select(Document).where(Document.user_id == user_id)
        if knowledge_base_id is not None:
            stmt = stmt.where(Document.knowledge_base_id == knowledge_base_id)
        stmt = stmt.order_by(Document.created_at.desc())
        return list(self.db.scalars(stmt))

    def get_by_id(self, user_id: int, document_id: int) -> Document | None:
        stmt = select(Document).where(Document.id == document_id, Document.user_id == user_id)
        return self.db.scalar(stmt)

    def create(
        self,
        user_id: int,
        knowledge_base_id: int,
        original_name: str,
        file_type: str,
        file_path: str,
        file_size: int | None,
    ) -> Document:
        document = Document(
            user_id=user_id,
            knowledge_base_id=knowledge_base_id,
            file_name=original_name,
            file_type=file_type,
            file_path=file_path,
            file_size=file_size,
            status="pending",
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def delete(self, user_id: int, document_id: int) -> bool:
        document = self.get_by_id(user_id, document_id)
        if not document:
            return False
        ChromaVectorStore().delete_document_chunks(document.id)
        file_path = Path(document.file_path)
        if file_path.exists():
            file_path.unlink()
        self.db.delete(document)
        self.db.commit()
        return True
