"""
ScholarGraph AI — Application Configuration
Centralized settings management using Pydantic BaseSettings.
All sensitive values are loaded from environment variables / .env file.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable loading."""

    # ── Application ──────────────────────────────────────────────
    APP_NAME: str = "ScholarGraph AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── Authentication ───────────────────────────────────────────
    JWT_SECRET_KEY: str = "scholargraph-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── OpenAI ───────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # ── Sentence Transformers ────────────────────────────────────
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # ── Pinecone ─────────────────────────────────────────────────
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX_NAME: str = "scholargraph"
    PINECONE_ENVIRONMENT: str = "us-east-1"
    PINECONE_METRIC: str = "cosine"

    # ── Database ─────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./scholargraph.db"
    POSTGRES_URL: Optional[str] = None

    # ── Redis ────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── File Upload ──────────────────────────────────────────────
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: list = [".pdf", ".png", ".jpg", ".jpeg", ".docx"]

    # ── Scoring Engine ───────────────────────────────────────────
    FREQUENCY_WEIGHT: float = 0.40
    SEMANTIC_WEIGHT: float = 0.35
    RECENCY_WEIGHT: float = 0.25
    RECENCY_DECAY_FACTOR: float = 0.85

    # ── RAG Configuration ────────────────────────────────────────
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64
    TOP_K_RETRIEVAL: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
