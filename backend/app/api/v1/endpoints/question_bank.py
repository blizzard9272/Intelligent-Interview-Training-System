from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.question_bank import QuestionBankGenerateRequest, QuestionBankItemResponse
from app.services.question_bank_service import QuestionBankService

router = APIRouter()


@router.post("/generate")
def generate_questions(
    payload: QuestionBankGenerateRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return QuestionBankService(db).create_generation_task(current_user.id, payload)


@router.get("", response_model=list[QuestionBankItemResponse])
def list_questions(
    knowledge_base_id: int | None = None,
    document_id: int | None = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return QuestionBankService(db).list_items(current_user.id, knowledge_base_id, document_id)
