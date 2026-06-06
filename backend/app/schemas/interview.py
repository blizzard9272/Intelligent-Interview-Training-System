from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class InterviewStartRequest(BaseModel):
    knowledge_base_id: int
    question_id: int | None = None
    difficulty: str | None = None
    question_type: str | None = None


class InterviewStartResponse(BaseModel):
    session_id: str
    knowledge_base_id: int
    question_id: int
    question: str
    difficulty: str | None = None
    question_tags: list[str] = Field(default_factory=list)
    status: str
    started_at: datetime


class InterviewAnswerRequest(BaseModel):
    session_id: str
    answer: str = Field(min_length=1)


class InterviewFeedbackResponse(BaseModel):
    session_id: str
    question_id: int
    question: str
    difficulty: str | None = None
    question_tags: list[str] = Field(default_factory=list)
    answer: str
    feedback: str
    overall_score: int
    strengths: list[str]
    improvements: list[str]
    suggested_followup: str | None = None
    next_question: str | None = None
    current_round: int
    max_rounds: int
    can_continue: bool
    status: str
    summary: str | None = None
    summary_meta: dict | None = None
    updated_at: datetime


class InterviewTurnResponse(BaseModel):
    id: int
    role: str
    content: str
    meta_json: dict | list | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class InterviewSessionListItemResponse(BaseModel):
    session_id: str
    knowledge_base_id: int
    question_id: int
    question: str
    difficulty: str | None = None
    question_tags: list[str] = Field(default_factory=list)
    status: str
    overall_score: int | None = None
    started_at: datetime
    updated_at: datetime
    current_round: int


class InterviewSessionDetailResponse(BaseModel):
    session_id: str
    knowledge_base_id: int
    question_id: int
    question: str
    difficulty: str | None = None
    question_tags: list[str] = Field(default_factory=list)
    reference_answer: str | None = None
    answer: str | None = None
    feedback: str | None = None
    overall_score: int | None = None
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    suggested_followup: str | None = None
    next_question: str | None = None
    current_round: int
    max_rounds: int
    can_continue: bool
    status: str
    summary: str | None = None
    summary_meta: dict | None = None
    started_at: datetime
    updated_at: datetime
    turns: list[InterviewTurnResponse] = Field(default_factory=list)
