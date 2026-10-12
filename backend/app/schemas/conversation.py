from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.chat import CitationItem

class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    citations: list[CitationItem] = []
    confidence_score: Optional[float] = None
    is_refusal: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ConversationResponse(BaseModel):
    id: str
    deployment_id: str
    title: str
    messages: list[MessageResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ConversationSummary(BaseModel):
    id: str
    deployment_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    model_config = ConfigDict(from_attributes=True)
