from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "CiteBot"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR}/citebot.db"

    # Uploads & Storage
    STORAGE_DIR: str = str(BASE_DIR / "storage")
    MAX_FILE_SIZE_MB: int = 25
    ALLOWED_EXTENSIONS: list[str] = [".pdf", ".docx", ".txt", ".md"]

    # RAG & Chunking
    CHUNK_SIZE_TOKENS: int = 400
    CHUNK_OVERLAP_TOKENS: int = 60
    DEFAULT_TOP_K: int = 6
    DEFAULT_CONFIDENCE_THRESHOLD: float = 0.45

    # LLM Settings
    LLM_PROVIDER: str = "mock"  # "openai", "gemini", or "mock" (for zero-config offline demo)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # Default Deployment Config
    DEFAULT_DEPLOYMENT_ID: str = "default"
    DEFAULT_CLIENT_NAME: str = "Acme Knowledge Base"
    DEFAULT_ACCENT_COLOR: str = "#2563EB"
    DEFAULT_REFUSAL_MESSAGE: str = "I couldn't find this information in the uploaded documents. Please try rephrasing or refer directly to your organization's documentation."
    DEFAULT_SYSTEM_TONE: str = "precise, helpful, and professional"
    DEFAULT_LANGUAGE: str = "en"

    # Security
    ADMIN_API_KEY: str = "citebot-admin-secret-key-change-me"
    RATE_LIMIT_PER_MINUTE: int = 60

settings = Settings()
