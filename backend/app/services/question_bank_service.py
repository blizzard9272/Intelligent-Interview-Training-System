from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.question_bank import QuestionBank
from app.schemas.question_bank import QuestionBankGenerateRequest


class QuestionBankService:
    def __init__(self, db: Session):
        self.db = db

    def create_generation_task(self, user_id: int, payload: QuestionBankGenerateRequest) -> dict:
        return {
            "message": "题目生成任务接口骨架已预留，后续接入异步任务和大模型抽题逻辑。",
            "user_id": user_id,
            "knowledge_base_id": payload.knowledge_base_id,
            "document_id": payload.document_id,
            "status": "queued",
        }

    def list_items(self, user_id: int, knowledge_base_id: int | None, document_id: int | None) -> list[QuestionBank]:
        stmt = select(QuestionBank).where(QuestionBank.user_id == user_id)
        if knowledge_base_id is not None:
            stmt = stmt.where(QuestionBank.knowledge_base_id == knowledge_base_id)
        if document_id is not None:
            stmt = stmt.where(QuestionBank.source_document_id == document_id)
        stmt = stmt.order_by(QuestionBank.created_at.desc())
        return list(self.db.scalars(stmt))
