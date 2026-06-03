from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.document import Document
from app.db.models.ingestion_task import IngestionTask


class IngestionTaskService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, document_id: int) -> IngestionTask:
        task = IngestionTask(
            document_id=document_id,
            status="queued",
            progress=0,
            message="等待入库处理",
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def list_by_user(self, user_id: int) -> list[IngestionTask]:
        stmt = (
            select(IngestionTask)
            .join(Document, IngestionTask.document_id == Document.id)
            .where(Document.user_id == user_id)
            .order_by(IngestionTask.created_at.desc())
        )
        return list(self.db.scalars(stmt))

    def list_by_document(self, user_id: int, document_id: int) -> list[IngestionTask]:
        stmt = (
            select(IngestionTask)
            .join(Document, IngestionTask.document_id == Document.id)
            .where(Document.user_id == user_id, IngestionTask.document_id == document_id)
            .order_by(IngestionTask.created_at.desc())
        )
        return list(self.db.scalars(stmt))

    def get_by_id(self, user_id: int, task_id: int) -> IngestionTask | None:
        stmt = (
            select(IngestionTask)
            .join(Document, IngestionTask.document_id == Document.id)
            .where(IngestionTask.id == task_id, Document.user_id == user_id)
        )
        return self.db.scalar(stmt)
