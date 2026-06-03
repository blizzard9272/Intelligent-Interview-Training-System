from datetime import datetime

from pydantic import BaseModel, Field


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    job_role: str | None = Field(default=None, max_length=100)


class KnowledgeBaseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    job_role: str | None = Field(default=None, max_length=100)


class KnowledgeBaseResponse(BaseModel):
    id: int
    name: str
    description: str | None
    job_role: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
