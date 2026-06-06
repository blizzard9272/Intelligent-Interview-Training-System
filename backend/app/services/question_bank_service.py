from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.question_bank import QuestionBank
from app.schemas.question_bank import QuestionBankGenerateRequest
from app.utils import get_agent_config, get_prompt_text


class QuestionBankService:
    def __init__(self, db: Session):
        self.db = db

    def create_generation_task(self, user_id: int, payload: QuestionBankGenerateRequest) -> dict:
        question_generation_config = get_agent_config().question_generation
        if question_generation_config.enabled:
            message = "Question generation task has been queued."
        else:
            message = "Question generation is disabled in agent.yaml."

        return {
            "message": message,
            "user_id": user_id,
            "knowledge_base_id": payload.knowledge_base_id,
            "document_id": payload.document_id,
            "status": "queued",
            "enabled": question_generation_config.enabled,
            "default_difficulty": question_generation_config.default_difficulty,
            "max_questions_per_document": question_generation_config.max_questions_per_document,
            "prompt_preview": get_prompt_text("question_generation"),
        }

    def list_items(self, user_id: int, knowledge_base_id: int | None, document_id: int | None) -> list[QuestionBank]:
        stmt = select(QuestionBank).where(QuestionBank.user_id == user_id)
        if knowledge_base_id is not None:
            stmt = stmt.where(QuestionBank.knowledge_base_id == knowledge_base_id)
        if document_id is not None:
            stmt = stmt.where(QuestionBank.source_document_id == document_id)
        stmt = stmt.order_by(QuestionBank.created_at.desc())
        return list(self.db.scalars(stmt))
