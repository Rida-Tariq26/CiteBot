from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class UsageLogResponse(BaseModel):
    id: str
    deployment_id: str
    conversation_id: Optional[str] = None
    query_text: str
    response_summary: str
    citation_count: int
    confidence_score: Optional[float] = None
    is_refusal: bool
    latency_ms: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UsageLogListResponse(BaseModel):
    logs: list[UsageLogResponse]
    total: int
    total_queries: int
    refusal_rate: float
    avg_latency_ms: float
