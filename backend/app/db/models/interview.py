from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin


class InterviewSession(TimestampMixin, Base):
    __tablename__ = "interview_sessions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    knowledge_base_id: Mapped[int] = mapped_column(ForeignKey("knowledge_bases.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("question_bank.id", ondelete="CASCADE"), index=True)
    question: Mapped[str] = mapped_column(Text())
    reference_answer: Mapped[str | None] = mapped_column(Text(), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="question_selected")
    overall_score: Mapped[int | None] = mapped_column(nullable=True)
    strengths: Mapped[list | None] = mapped_column(JSON, nullable=True)
    improvements: Mapped[list | None] = mapped_column(JSON, nullable=True)
    suggested_followup: Mapped[str | None] = mapped_column(Text(), nullable=True)
    started_at: Mapped[datetime] = mapped_column(nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(nullable=True)

    user = relationship("User", back_populates="interview_sessions")
    knowledge_base = relationship("KnowledgeBase", back_populates="interview_sessions")
    question_bank_item = relationship("QuestionBank", back_populates="interview_sessions")
    turns = relationship("InterviewTurn", back_populates="session", cascade="all, delete-orphan")


class InterviewTurn(Base):
    __tablename__ = "interview_turns"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("interview_sessions.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(30))
    content: Mapped[str] = mapped_column(Text())
    meta_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    session = relationship("InterviewSession", back_populates="turns")
