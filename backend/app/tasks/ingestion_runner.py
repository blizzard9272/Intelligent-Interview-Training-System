from app.db.session import SessionLocal
from app.services.ingestion_service import IngestionService


def run_ingestion_job(document_id: int, task_id: int) -> None:
    db = SessionLocal()
    try:
        IngestionService(db).process_document(document_id=document_id, task_id=task_id)
    finally:
        db.close()
