"""
知识库请求与响应模型定义，使用Pydantic的BaseModel类创建数据模型，用于验证和序列化与知识库相关的API请求和响应数据。
"""
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


class DocumentChunkResponse(BaseModel):
    chunk_index: int
    section_title: str | None = None
    page_no: int | None = None
    content: str
