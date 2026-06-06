"""
任务接口，定义了与文档处理相关的API端点。
负责：
1. 列出任务：提供一个GET /tasks端点，返回当前用户创建的所有文档处理任务的列表，可以根据文档ID进行过滤。
2. 获取任务详情：提供一个GET /tasks/{task_id}端点，返回指定任务的详细信息。
3. 错误处理：在获取任务详情过程中，如果指定的任务不存在，返回适当的HTTP错误响应，提示用户相关问题。
"""

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
