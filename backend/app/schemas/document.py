from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: int
    knowledge_base_id: int
    file_name: str
    file_type: str
    file_path: str
    file_size: int | None
    status: str
    parse_error: str | None
    chunk_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentUploadResponse(BaseModel):
    document_id: int
    task_id: int
    status: str
