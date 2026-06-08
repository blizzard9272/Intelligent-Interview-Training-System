from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.interview import (
    InterviewAnswerRequest,
    InterviewFeedbackResponse,
    InterviewSessionDetailResponse,
    InterviewSessionListItemResponse,
    InterviewStartRequest,
    InterviewStartResponse,
    TrainingAnalysisResponse,
)
from app.services.interview_service import InterviewService

router = APIRouter()


@router.post("/start", response_model=InterviewStartResponse)
def start_interview(
    payload: InterviewStartRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return InterviewService(db).start_session(current_user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/answer", response_model=InterviewFeedbackResponse)
def answer_interview(
    payload: InterviewAnswerRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return InterviewService(db).submit_answer(current_user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/sessions", response_model=list[InterviewSessionListItemResponse])
def list_interview_sessions(
    knowledge_base_id: int | None = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return InterviewService(db).list_sessions(current_user.id, knowledge_base_id)


@router.get("/analysis", response_model=TrainingAnalysisResponse)
def get_training_analysis(
    knowledge_base_id: int | None = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return InterviewService(db).analyze_training(current_user.id, knowledge_base_id)


@router.get("/sessions/{session_id}", response_model=InterviewSessionDetailResponse)
def get_interview_session(
    session_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = InterviewService(db).get_session(current_user.id, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="面试会话不存在")
    return session


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_interview_session(
    session_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deleted = InterviewService(db).delete_session(current_user.id, session_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="面试会话不存在")
