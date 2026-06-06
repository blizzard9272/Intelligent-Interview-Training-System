"""
文档接口，定义了与文档相关的API端点。
负责：
1. 列出文档：提供一个GET /documents端点，返回当前用户创建的所有文档的列表，可以根据知识库ID进行过滤。
2. 上传文档：提供一个POST /documents/upload端点，接受文档文件和所属知识库ID，将文档保存到服务器，并创建文档记录，同时触发后台任务进行文档处理。
3. 获取文档详情：提供一个GET /documents/{document_id}端点，返回指定文档的详细信息。
4. 删除文档：提供一个DELETE /documents/{document_id}端点，删除指定的文档记录和对应的文件。
5. error处理：在上传、获取和删除过程中，如果发生错误（如文件类型不支持、知识库不存在、文档不存在等），返回适当的HTTP错误响应，提示用户相关问题。
"""
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.document import DocumentChunkResponse, DocumentResponse, DocumentUploadResponse
from app.services.document_service import DocumentService
from app.services.kb_service import KnowledgeBaseService
from app.services.task_service import IngestionTaskService
from app.tasks.ingestion_runner import run_ingestion_job
from app.utils import get_ingestion_config, save_upload_file

router = APIRouter()
logger = logging.getLogger("app.api.documents")


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
    logger.info(
        "document_upload_started user_id=%s knowledge_base_id=%s filename=%s content_type=%s",
        current_user.id,
        knowledge_base_id,
        file.filename,
        file.content_type,
    )
    kb = KnowledgeBaseService(db).get_by_id(current_user.id, knowledge_base_id)
    if not kb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found")

    ingestion_config = get_ingestion_config()
    if ingestion_config.pipeline.async_mode != "background_tasks":
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unsupported ingestion mode")

    saved_upload = await save_upload_file(file)

    document = DocumentService(db).create(
        user_id=current_user.id,
        knowledge_base_id=knowledge_base_id,
        original_name=file.filename,
        file_type=saved_upload.file_type,
        file_path=str(saved_upload.path),
        file_size=saved_upload.size,
    )
    task = IngestionTaskService(db).create(document.id)
    background_tasks.add_task(run_ingestion_job, document.id, task.id)
    logger.info(
        "document_upload_completed user_id=%s knowledge_base_id=%s document_id=%s task_id=%s file_type=%s size=%s",
        current_user.id,
        knowledge_base_id,
        document.id,
        task.id,
        saved_upload.file_type,
        saved_upload.size,
    )
    return DocumentUploadResponse(document_id=document.id, task_id=task.id, status=task.status)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    document = DocumentService(db).get_by_id(current_user.id, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.get("/{document_id}/chunks", response_model=list[DocumentChunkResponse])
def get_document_chunks(document_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    document = DocumentService(db).get_by_id(current_user.id, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return DocumentService(db).get_chunks(current_user.id, document_id)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    deleted = DocumentService(db).delete(current_user.id, document_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
