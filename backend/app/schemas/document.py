from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class DocumentResponse(BaseModel):
    id: str
    deployment_id: str
    filename: str
    file_type: str
    file_size_bytes: int
    status: str
    error_message: Optional[str] = None
    chunk_count: int
    page_count: int
    upload_date: datetime

    model_config = ConfigDict(from_attributes=True)

class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int

class ReindexResponse(BaseModel):
    status: str
    processed_count: int
    total_chunks: int
