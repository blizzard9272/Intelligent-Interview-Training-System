"""
知识库接口，定义了与知识库相关的API端点。
负责：
1. 列出知识库：提供一个GET /knowledge-bases端点，返回当前用户创建的所有知识库的列表。
2. 创建知识库：提供一个POST /knowledge-bases端点，接受知识库的名称和描述，创建一个新的知识库，并返回创建的知识库信息。
3. 更新知识库：提供一个PUT /knowledge-bases/{kb_id}端点，接受知识库ID和更新后的信息，更新指定的知识库，并返回更新后的知识库信息。
4. 删除知识库：提供一个DELETE /knowledge-bases/{kb_id}端点，接受知识库ID，删除指定的知识库，并返回204 No Content响应。
5. 错误处理：在更新和删除过程中，如果指定的知识库不存在，返回适当的HTTP错误响应，提示用户相关问题。
"""
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
