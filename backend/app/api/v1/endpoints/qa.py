import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
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


@router.post("/ask/stream")
def ask_question_stream(payload: AskRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        result = QAService(db).ask(current_user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    def event_stream():
        yield _sse_event(
            "meta",
            {
                "session_id": result.session_id,
            },
        )
        chunk_size = 80
        answer = result.answer or ""
        for index in range(0, len(answer), chunk_size):
            yield _sse_event(
                "delta",
                {
                    "content": answer[index : index + chunk_size],
                },
            )
        yield _sse_event(
            "final",
            {
                "session_id": result.session_id,
                "references": [item.model_dump() for item in result.references],
                "debug_trace": result.debug_trace.model_dump() if result.debug_trace else None,
            },
        )

    return StreamingResponse(event_stream(), media_type="text/event-stream")


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


def _sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
