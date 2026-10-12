import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Deployment(Base):
    __tablename__ = "deployments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    client_name: Mapped[str] = mapped_column(String(255), nullable=False, default="Knowledge Assistant")
    logo_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    accent_color: Mapped[str] = mapped_column(String(32), default="#2563EB")
    confidence_threshold: Mapped[float] = mapped_column(Float, default=0.45)
    refusal_message: Mapped[str] = mapped_column(
        Text,
        default="I couldn't find this information in the uploaded documents. Please try rephrasing or refer directly to your organization's documentation."
    )
    system_tone: Mapped[str] = mapped_column(String(128), default="precise, helpful, and professional")
    language: Mapped[str] = mapped_column(String(16), default="en")
    starter_prompts: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    documents = relationship("Document", back_populates="deployment", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="deployment", cascade="all, delete-orphan")
    logs = relationship("UsageLog", back_populates="deployment", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    deployment_id: Mapped[str] = mapped_column(String(64), ForeignKey("deployments.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(32), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="processing")  # processing, ready, failed
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    page_count: Mapped[int] = mapped_column(Integer, default=1)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    upload_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    deployment = relationship("Deployment", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")

class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    document_id: Mapped[str] = mapped_column(String(64), ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    deployment_id: Mapped[str] = mapped_column(String(64), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    section_heading: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    document = relationship("Document", back_populates="chunks")

class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    deployment_id: Mapped[str] = mapped_column(String(64), ForeignKey("deployments.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255), default="New Chat")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    deployment = relationship("Deployment", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    conversation_id: Mapped[str] = mapped_column(String(64), ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False)  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[list] = mapped_column(JSON, default=list)  # list of resolved citations
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_refusal: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    conversation = relationship("Conversation", back_populates="messages")

class UsageLog(Base):
    __tablename__ = "usage_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    deployment_id: Mapped[str] = mapped_column(String(64), ForeignKey("deployments.id", ondelete="CASCADE"), index=True)
    conversation_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    response_summary: Mapped[str] = mapped_column(Text, nullable=False)
    citation_count: Mapped[int] = mapped_column(Integer, default=0)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_refusal: Mapped[bool] = mapped_column(Boolean, default=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    deployment = relationship("Deployment", back_populates="logs")
