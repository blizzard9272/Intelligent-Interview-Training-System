from datetime import datetime

from pydantic import BaseModel


class IngestionTaskResponse(BaseModel):
    id: int
    document_id: int
    status: str
    progress: int
    message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
