from typing import Optional
from pydantic import BaseModel, Field

class CitationItem(BaseModel):
    citation_number: int = Field(..., description="The inline citation number e.g. 1 for [1]")
    chunk_id: str = Field(..., description="ID of the source chunk")
    document_id: str = Field(..., description="ID of the parent document")
    document_name: str = Field(..., description="Name of the document")
    page_number: Optional[int] = Field(None, description="Page number if applicable")
    section_heading: Optional[str] = Field(None, description="Section heading if found")
    excerpt: str = Field(..., description="The exact passage or excerpt supporting the fact")
    similarity_score: Optional[float] = Field(None, description="Relevance similarity score")

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User's query")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID or null for new")
    deployment_id: Optional[str] = Field(None, description="Deployment ID if multi-tenant")

class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    content: str
    citations: list[CitationItem] = []
    is_refusal: bool = False
    confidence_score: Optional[float] = None
    has_conflicts: bool = False
