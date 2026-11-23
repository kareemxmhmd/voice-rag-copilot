"""Centralized configuration and settings for Voice RAG Copilot."""

import os
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Determine project base directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Base Paths
    project_root: Path = Field(default=PROJECT_ROOT)
    data_dir: Path = Field(default=PROJECT_ROOT / "data")
    raw_data_dir: Path = Field(default=PROJECT_ROOT / "data" / "raw")
    eval_data_dir: Path = Field(default=PROJECT_ROOT / "data" / "eval")
    vector_store_dir: Path = Field(default=PROJECT_ROOT / "vector_store")
    reports_dir: Path = Field(default=PROJECT_ROOT / "evaluation" / "reports")

    # API Keys
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")

    # LLM & Embedding Models
    gemini_model: str = Field(default="gemini-3.5-flash-lite", alias="GEMINI_MODEL")
    embedding_model: str = Field(default="gemini-embedding-001", alias="EMBEDDING_MODEL")

    # Vector Store & Retrieval Settings
    collection_name: str = Field(default="ecommerce_knowledge_base", alias="COLLECTION_NAME")
    chunk_size: int = Field(default=500, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=50, alias="CHUNK_OVERLAP")
    top_k: int = Field(default=3, alias="TOP_K")

    # Voice / Audio Settings
    whisper_model: str = Field(default="base", alias="WHISPER_MODEL")
    tts_voice: str = Field(default="en-US-JennyNeural", alias="TTS_VOICE")
    tts_rate: str = Field(default="+0%", alias="TTS_RATE")

    # Application & Logging
    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    def ensure_directories(self) -> None:
        """Create required runtime directories if they do not exist."""
        for path in [
            self.data_dir,
            self.raw_data_dir,
            self.eval_data_dir,
            self.vector_store_dir,
            self.reports_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)


# Global singleton instance
settings = Settings()
settings.ensure_directories()
