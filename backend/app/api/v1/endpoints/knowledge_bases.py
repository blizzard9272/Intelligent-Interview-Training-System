from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseResponse, KnowledgeBaseUpdate
from app.services.kb_service import KnowledgeBaseService

router = APIRouter()


@router.get("", response_model=list[KnowledgeBaseResponse])
def list_knowledge_bases(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return KnowledgeBaseService(db).list_by_user(current_user.id)


@router.post("", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge_base(
    payload: KnowledgeBaseCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return KnowledgeBaseService(db).create(current_user.id, payload)


@router.put("/{kb_id}", response_model=KnowledgeBaseResponse)
def update_knowledge_base(
    kb_id: int,
    payload: KnowledgeBaseUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = KnowledgeBaseService(db)
    kb = service.update(current_user.id, kb_id, payload)
    if not kb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在")
    return kb


@router.delete("/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_base(kb_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    deleted = KnowledgeBaseService(db).delete(current_user.id, kb_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在")
