from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.task import IngestionTaskResponse
from app.services.task_service import IngestionTaskService

router = APIRouter()


@router.get("", response_model=list[IngestionTaskResponse])
def list_tasks(
    document_id: int | None = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = IngestionTaskService(db)
    if document_id is not None:
        return service.list_by_document(current_user.id, document_id)
    return service.list_by_user(current_user.id)


@router.get("/{task_id}", response_model=IngestionTaskResponse)
def get_task(task_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    task = IngestionTaskService(db).get_by_id(current_user.id, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task
