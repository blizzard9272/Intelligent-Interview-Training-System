from app.tasks.celery_app import celery_app
from app.tasks.ingestion_runner import run_ingestion_job


@celery_app.task(name="ingestion.process_document")
def process_document(document_id: int, task_id: int) -> dict:
    run_ingestion_job(document_id=document_id, task_id=task_id)
    return {
        "document_id": document_id,
        "task_id": task_id,
        "status": "completed",
        "message": "Ingestion task executed",
    }
