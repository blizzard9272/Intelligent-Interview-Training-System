from datetime import datetime

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    knowledge_base_id: int
    question: str = Field(min_length=1)
    session_id: int | None = None


class QAReference(BaseModel):
    document_id: int
    file_name: str
    chunk_index: int
    snippet: str
    section_title: str | None = None
    content_type_hint: str | None = None
    document_kind: str | None = None
    starts_with_question: bool | None = None
    context_role: str | None = None


class QARetrievalCandidate(BaseModel):
    file_name: str
    chunk_index: int
    section_title: str | None = None
    content_type_hint: str | None = None
    document_kind: str | None = None
    context_role: str | None = None
    distance: float | None = None
    retrieval_rank: int | None = None
    rerank_score: float | None = None
    matched_filters: dict[str, object] | None = None


class QARetrievalStep(BaseModel):
    filters: dict[str, object]
    returned_count: int
    candidates: list[QARetrievalCandidate]


class QAContextBlock(BaseModel):
    role: str
    title: str
    references: list[QAReference]


class QADebugTrace(BaseModel):
    route_intent: str
    rerank_enabled: bool
    query_plan: list[dict[str, object]]
    retrieval_steps: list[QARetrievalStep]
    reranked_results: list[QARetrievalCandidate]
    context_blocks: list[QAContextBlock]
    structured_context: str


class AskResponse(BaseModel):
    session_id: int
    answer: str
    references: list[QAReference]
    debug_trace: QADebugTrace | None = None


class QAMessageResponse(BaseModel):
    role: str
    content: str
    references_json: list[QAReference] | None = None
    debug_trace: QADebugTrace | None = None


class QASessionResponse(BaseModel):
    id: int
    knowledge_base_id: int
    title: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class QASessionDetailResponse(BaseModel):
    id: int
    knowledge_base_id: int
    title: str | None
    messages: list[QAMessageResponse]
