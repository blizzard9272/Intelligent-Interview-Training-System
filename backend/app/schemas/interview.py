from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class InterviewStartRequest(BaseModel):
    knowledge_base_id: int
    question_id: int | None = None
    source_document_id: int | None = None
    focus_topic: str | None = None
    difficulty: str | None = None
    question_type: str | None = None
    question_strategy: str | None = None
    drill_mode: str | None = None
    question_count: int | None = None


class InterviewStartResponse(BaseModel):
    session_id: str
    knowledge_base_id: int
    question_id: int
    question: str
    source_document_id: int | None = None
    source_document_name: str | None = None
    focus_topic: str | None = None
    difficulty: str | None = None
    question_tags: list[str] = Field(default_factory=list)
    question_strategy: str
    drill_mode: str
    question_count: int
    active_question_number: int
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
    next_prompt_type: str | None = None
    current_round: int
    max_rounds: int
    can_continue: bool
    drill_mode: str
    question_count: int
    active_question_number: int
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
    source_document_id: int | None = None
    source_document_name: str | None = None
    focus_topic: str | None = None
    difficulty: str | None = None
    question_tags: list[str] = Field(default_factory=list)
    question_strategy: str
    drill_mode: str
    question_count: int
    active_question_number: int
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
    source_document_id: int | None = None
    source_document_name: str | None = None
    focus_topic: str | None = None
    difficulty: str | None = None
    question_tags: list[str] = Field(default_factory=list)
    question_strategy: str
    drill_mode: str
    question_count: int
    active_question_number: int
    reference_answer: str | None = None
    answer: str | None = None
    feedback: str | None = None
    overall_score: int | None = None
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    suggested_followup: str | None = None
    next_question: str | None = None
    next_prompt_type: str | None = None
    current_round: int
    max_rounds: int
    can_continue: bool
    status: str
    summary: str | None = None
    summary_meta: dict | None = None
    started_at: datetime
    updated_at: datetime
    turns: list[InterviewTurnResponse] = Field(default_factory=list)


class TrainingAnalysisCountItem(BaseModel):
    label: str
    count: int


class TrainingAnalysisScorePoint(BaseModel):
    session_id: str
    score: int
    started_at: datetime


class TrainingDrillRecommendation(BaseModel):
    focus_label: str
    title: str
    description: str
    knowledge_base_id: int | None = None
    source_document_id: int | None = None
    source_document_name: str | None = None
    question_type: str | None = None
    drill_mode: str
    question_count: int
    question_strategy: str


class TrainingFocusEffectItem(BaseModel):
    focus_label: str
    session_count: int
    average_score: float
    latest_score: int
    best_score: int
    score_delta: float
    last_practiced_at: datetime


class TrainingAnalysisResponse(BaseModel):
    knowledge_base_id: int | None = None
    total_sessions: int
    completed_sessions: int
    average_score: float | None = None
    latest_score: int | None = None
    common_weak_points: list[TrainingAnalysisCountItem] = Field(default_factory=list)
    common_strengths: list[TrainingAnalysisCountItem] = Field(default_factory=list)
    question_type_breakdown: list[TrainingAnalysisCountItem] = Field(default_factory=list)
    source_document_breakdown: list[TrainingAnalysisCountItem] = Field(default_factory=list)
    recent_scores: list[TrainingAnalysisScorePoint] = Field(default_factory=list)
    recommended_focus: list[str] = Field(default_factory=list)
    focus_drills: list[TrainingDrillRecommendation] = Field(default_factory=list)
    focus_drill_effects: list[TrainingFocusEffectItem] = Field(default_factory=list)
