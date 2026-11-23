"""FastAPI REST Service for Voice RAG Copilot.

Exposes endpoints for health check, text querying, and voice/audio querying
with Base64 and direct audio streaming support.
"""

import base64
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from src.api.schemas import HealthResponse, LatencyMetrics, QueryResponse, SourceCitation, TextQueryRequest
from src.config import settings
from src.pipeline import get_pipeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager to warm up the pipeline and verify vector store."""
    print("--> Initializing Voice RAG Pipeline...")
    get_pipeline()
    print("--> Voice RAG Copilot API is ready.")
    yield
    print("--> Shutting down Voice RAG Copilot API.")


app = FastAPI(
    title="NovaCart Voice RAG Copilot API",
    description="Low-Latency Bilingual Voice RAG API for E-commerce & Subscription Operations",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for cross-origin web/mobile access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["General"])
async def root():
    """Welcome endpoint pointing to Swagger documentation."""
    return {
        "message": "Welcome to NovaCart Voice RAG Copilot API",
        "docs_url": "/docs",
        "health_url": "/health",
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """Returns service health status and vector store collection size."""
    try:
        pipeline = get_pipeline()
        vector_count = pipeline.generator.retriever.collection.count()
        return HealthResponse(
            status="ok",
            app_name="NovaCart Voice RAG Copilot",
            version="0.1.0",
            environment=settings.app_env,
            collection_name=settings.collection_name,
            vector_count=vector_count,
        )
    except Exception as exc:
        return HealthResponse(
            status=f"degraded: {exc}",
            app_name="NovaCart Voice RAG Copilot",
            version="0.1.0",
            environment=settings.app_env,
            collection_name=settings.collection_name,
            vector_count=0,
        )


@app.post("/ask-text", response_model=QueryResponse, tags=["RAG"])
async def ask_text(request: TextQueryRequest):
    """Process a text question through RAG and return spoken answer with optional audio."""
    try:
        pipeline = get_pipeline()
        res = pipeline.process_text(
            query=request.query,
            return_audio=request.return_audio,
            top_k=request.top_k,
            voice=request.voice,
        )

        audio_b64 = None
        if res.get("audio_bytes"):
            audio_b64 = base64.b64encode(res["audio_bytes"]).decode("utf-8")

        citations = [
            SourceCitation(
                source=c.get("source", "unknown"),
                doc_title=c.get("doc_title", ""),
                section=c.get("section", ""),
                score=c.get("score", 0.0),
            )
            for c in res.get("retrieved_chunks", [])
        ]

        return QueryResponse(
            query=res["query"],
            answer=res["answer"],
            sources=res["sources"],
            citations=citations,
            latencies=LatencyMetrics(**res["latencies"]),
            audio_base64=audio_b64,
            audio_format=res.get("audio_format", "audio/mp3"),
            voice=res.get("voice"),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing text query: {str(exc)}",
        )


@app.post("/ask-voice", response_model=QueryResponse, tags=["Voice"])
async def ask_voice(
    file: UploadFile = File(..., description="Audio recording file (WAV, MP3, WebM, OGG)"),
    return_audio: bool = Form(True, description="Whether to synthesize spoken audio response"),
    top_k: int = Form(3, ge=1, le=10, description="Top-k context chunks to retrieve"),
    voice: Optional[str] = Form(None, description="Optional manual voice override"),
):
    """Process a voice audio recording through STT -> RAG -> TTS and return answer and audio."""
    try:
        audio_bytes = await file.read()
        if not audio_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded audio file is empty.",
            )

        mime_type = file.content_type or "audio/wav"

        pipeline = get_pipeline()
        res = pipeline.process_voice(
            audio_input=audio_bytes,
            mime_type=mime_type,
            return_audio=return_audio,
            top_k=top_k,
            voice=voice,
        )

        audio_b64 = None
        if res.get("audio_bytes"):
            audio_b64 = base64.b64encode(res["audio_bytes"]).decode("utf-8")

        citations = [
            SourceCitation(
                source=c.get("source", "unknown"),
                doc_title=c.get("doc_title", ""),
                section=c.get("section", ""),
                score=c.get("score", 0.0),
            )
            for c in res.get("retrieved_chunks", [])
        ]

        return QueryResponse(
            query=res["query"],
            answer=res["answer"],
            sources=res["sources"],
            citations=citations,
            latencies=LatencyMetrics(**res["latencies"]),
            audio_base64=audio_b64,
            audio_format=res.get("audio_format", "audio/mp3"),
            voice=res.get("voice"),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing voice input: {str(exc)}",
        )


@app.post("/ask-voice/audio-stream", tags=["Voice"])
async def ask_voice_audio_stream(
    file: UploadFile = File(..., description="Audio recording file"),
    top_k: int = Form(3),
):
    """Directly streams the synthesized MP3 audio reply bytes for voice players."""
    try:
        audio_bytes = await file.read()
        mime_type = file.content_type or "audio/wav"

        pipeline = get_pipeline()
        res = pipeline.process_voice(
            audio_input=audio_bytes,
            mime_type=mime_type,
            return_audio=True,
            top_k=top_k,
        )

        if not res.get("audio_bytes"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate audio reply.",
            )

        return Response(
            content=res["audio_bytes"],
            media_type="audio/mpeg",
            headers={
                "X-Transcribed-Query": res.get("query", "").encode("utf-8").decode("latin-1", "ignore"),
                "X-Total-Latency-Ms": str(res["latencies"]["total_ms"]),
            },
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
