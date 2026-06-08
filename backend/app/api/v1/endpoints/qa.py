from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.qa import AskRequest, AskResponse, QASessionDetailResponse, QASessionResponse
from app.services.qa_service import QAService

router = APIRouter()


@router.post("/ask", response_model=AskResponse)
def ask_question(payload: AskRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return QAService(db).ask(current_user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/sessions", response_model=list[QASessionResponse])
def list_sessions(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return QAService(db).list_sessions(current_user.id)


@router.get("/sessions/{session_id}", response_model=QASessionDetailResponse)
def get_session(session_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    session = QAService(db).get_session_detail(current_user.id, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    deleted = QAService(db).delete_session(current_user.id, session_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
