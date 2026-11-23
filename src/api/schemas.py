"""Pydantic schemas and data contracts for Voice RAG Copilot FastAPI service."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = Field(default="ok", examples=["ok"])
    app_name: str = Field(default="Voice RAG Copilot", examples=["Voice RAG Copilot"])
    version: str = Field(default="0.1.0", examples=["0.1.0"])
    environment: str = Field(default="development", examples=["development"])
    collection_name: str = Field(default="ecommerce_knowledge_base")
    vector_count: int = Field(default=81, examples=[81])


class LatencyMetrics(BaseModel):
    """Latency breakdown per pipeline stage in milliseconds."""

    stt_ms: float = Field(default=0.0, description="Speech-to-Text transcription latency (ms)")
    retrieval_ms: float = Field(default=0.0, description="ChromaDB vector retrieval latency (ms)")
    llm_ms: float = Field(default=0.0, description="LLM generation latency (ms)")
    tts_ms: float = Field(default=0.0, description="Text-to-Speech audio synthesis latency (ms)")
    total_ms: float = Field(default=0.0, description="Total pipeline latency (ms)")


class TextQueryRequest(BaseModel):
    """Request model for text-based queries."""

    query: str = Field(
        ...,
        min_length=1,
        examples=["What was Basic churn in Q3, and what is the average LTV for Basic versus Pro?"],
        description="The customer or operations query in Arabic or English",
    )
    return_audio: bool = Field(
        default=True,
        description="Whether to synthesize and return an MP3 audio reply",
    )
    top_k: Optional[int] = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of context chunks to retrieve",
    )
    voice: Optional[str] = Field(
        default=None,
        description="Optional manual override for the TTS neural voice",
    )


class SourceCitation(BaseModel):
    """Metadata about a retrieved context document."""

    source: str
    doc_title: str
    section: str
    score: float


class QueryResponse(BaseModel):
    """Unified response model for text and voice queries."""

    query: str = Field(description="The original or transcribed user query")
    answer: str = Field(description="Voice-ready spoken answer from RAG")
    sources: List[str] = Field(description="Unique source files referenced")
    citations: List[SourceCitation] = Field(default_factory=list, description="Detailed citations")
    latencies: LatencyMetrics = Field(description="Per-stage latency breakdown")
    audio_base64: Optional[str] = Field(
        default=None,
        description="Base64-encoded MP3 audio for immediate browser playback",
    )
    audio_format: Optional[str] = Field(default="audio/mp3", description="Audio MIME format")
    voice: Optional[str] = Field(default=None, description="Neural voice model used for TTS")
