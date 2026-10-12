from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class DeploymentBase(BaseModel):
    client_name: str = Field(..., max_length=255)
    logo_url: Optional[str] = None
    accent_color: str = Field("#2563EB", pattern=r"^#[0-9a-fA-F]{6}$")
    confidence_threshold: float = Field(0.45, ge=0.0, le=1.0)
    refusal_message: str
    system_tone: str = "precise, helpful, and professional"
    language: str = "en"
    starter_prompts: list[str] = []

class DeploymentCreate(DeploymentBase):
    id: Optional[str] = None

class DeploymentUpdate(BaseModel):
    client_name: Optional[str] = None
    logo_url: Optional[str] = None
    accent_color: Optional[str] = None
    confidence_threshold: Optional[float] = None
    refusal_message: Optional[str] = None
    system_tone: Optional[str] = None
    language: Optional[str] = None
    starter_prompts: Optional[list[str]] = None

class DeploymentPublicConfig(BaseModel):
    id: str
    client_name: str
    logo_url: Optional[str]
    accent_color: str
    refusal_message: str
    starter_prompts: list[str]
    active_document_count: int = 0
    language: str

class DeploymentResponse(DeploymentBase):
    id: str
    created_at: datetime
    updated_at: datetime
    active_document_count: int = 0

    model_config = ConfigDict(from_attributes=True)
