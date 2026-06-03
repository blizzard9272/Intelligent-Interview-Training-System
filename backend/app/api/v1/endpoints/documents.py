from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.schemas.document import DocumentResponse, DocumentUploadResponse
from app.services.document_service import DocumentService
from app.services.kb_service import KnowledgeBaseService
from app.services.task_service import IngestionTaskService
from app.tasks.ingestion_runner import run_ingestion_job

router = APIRouter()

ALLOWED_SUFFIXES = {".txt", ".md", ".pdf"}


@router.get("", response_model=list[DocumentResponse])
def list_documents(
    knowledge_base_id: int | None = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return DocumentService(db).list_by_user(current_user.id, knowledge_base_id)


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    knowledge_base_id: int = Form(...),
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type")

    kb = KnowledgeBaseService(db).get_by_id(current_user.id, knowledge_base_id)
    if not kb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found")

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"{uuid4().hex}{suffix}"
    file_path = upload_dir / file_name
    content = await file.read()
    file_path.write_bytes(content)

    document = DocumentService(db).create(
        user_id=current_user.id,
        knowledge_base_id=knowledge_base_id,
        original_name=file.filename,
        file_type=suffix.lstrip("."),
        file_path=str(file_path),
        file_size=len(content),
    )
    task = IngestionTaskService(db).create(document.id)
    background_tasks.add_task(run_ingestion_job, document.id, task.id)
    return DocumentUploadResponse(document_id=document.id, task_id=task.id, status=task.status)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    document = DocumentService(db).get_by_id(current_user.id, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    deleted = DocumentService(db).delete(current_user.id, document_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
