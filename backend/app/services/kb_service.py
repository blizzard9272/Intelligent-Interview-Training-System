from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.knowledge_base import KnowledgeBase
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseUpdate


class KnowledgeBaseService:
    def __init__(self, db: Session):
        self.db = db

    def list_by_user(self, user_id: int) -> list[KnowledgeBase]:
        stmt = select(KnowledgeBase).where(KnowledgeBase.user_id == user_id).order_by(KnowledgeBase.created_at.desc())
        return list(self.db.scalars(stmt))

    def get_by_id(self, user_id: int, kb_id: int) -> KnowledgeBase | None:
        stmt = select(KnowledgeBase).where(KnowledgeBase.id == kb_id, KnowledgeBase.user_id == user_id)
        return self.db.scalar(stmt)

    def create(self, user_id: int, payload: KnowledgeBaseCreate) -> KnowledgeBase:
        kb = KnowledgeBase(user_id=user_id, **payload.model_dump())
        self.db.add(kb)
        self.db.commit()
        self.db.refresh(kb)
        return kb

    def update(self, user_id: int, kb_id: int, payload: KnowledgeBaseUpdate) -> KnowledgeBase | None:
        kb = self.get_by_id(user_id, kb_id)
        if not kb:
            return None
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(kb, key, value)
        self.db.commit()
        self.db.refresh(kb)
        return kb

    def delete(self, user_id: int, kb_id: int) -> bool:
        kb = self.get_by_id(user_id, kb_id)
        if not kb:
            return False
        self.db.delete(kb)
        self.db.commit()
        return True
