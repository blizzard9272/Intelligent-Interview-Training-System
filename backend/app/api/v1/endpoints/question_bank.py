"""
题库接口，定义了与题库相关的API端点。
负责：
1. 生成题目：提供一个POST /question-bank/generate端点，接受生成题目的请求参数（如知识库ID、文档ID、题目数量等），创建一个新的题目生成任务，并返回任务的相关信息。
2. 列出题目：提供一个GET /question-bank端点，返回当前用户创建的所有题目的列表，可以根据知识库ID和文档ID进行过滤。
3. 错误处理：在生成题目和列出题目的过程中，如果发生错误（如知识库不存在、文档不存在等），返回适当的HTTP错误响应，提示用户相关问题。
"""
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
