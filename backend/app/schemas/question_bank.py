from datetime import datetime

from pydantic import BaseModel


class QuestionBankGenerateRequest(BaseModel):
    knowledge_base_id: int
    document_id: int | None = None


class QuestionBankItemResponse(BaseModel):
    id: int
    knowledge_base_id: int
    source_document_id: int | None
    question: str
    reference_answer: str | None
    tags: list | None
    difficulty: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
