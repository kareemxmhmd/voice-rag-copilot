"""Full Voice RAG Pipeline Orchestrator.

Coordinates Audio Input -> STT -> RAG Retrieval -> LLM Generation -> TTS Audio Output
with latency breakdown and structured observability.
"""

from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Union

from src.rag.generator import VoiceRAGGenerator
from src.voice.stt import GeminiAudioSTT
from src.voice.tts import EdgeTTS


class VoiceRAGPipeline:
    """End-to-End Orchestrator for Voice RAG Copilot."""

    def __init__(
        self,
        stt: Optional[GeminiAudioSTT] = None,
        generator: Optional[VoiceRAGGenerator] = None,
        tts: Optional[EdgeTTS] = None,
    ):
        self.stt = stt or GeminiAudioSTT()
        self.generator = generator or VoiceRAGGenerator()
        self.tts = tts or EdgeTTS()

    def process_text(
        self,
        query: str,
        return_audio: bool = True,
        top_k: Optional[int] = None,
        voice: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process a text query through RAG and generate optional audio reply."""
        t_start = time.perf_counter()

        # 1. RAG Core (Retrieval + LLM Generation)
        rag_res = self.generator.generate(query, top_k=top_k)

        # 2. Text-to-Speech (TTS)
        audio_bytes: Optional[bytes] = None
        tts_ms = 0.0
        used_voice = None
        audio_format = None

        if return_audio and rag_res["answer"]:
            tts_res = self.tts.synthesize(rag_res["answer"], voice=voice)
            audio_bytes = tts_res["audio_bytes"]
            tts_ms = tts_res["tts_ms"]
            used_voice = tts_res["voice"]
            audio_format = tts_res["format"]

        total_ms = round((time.perf_counter() - t_start) * 1000, 2)

        latencies = {
            "stt_ms": 0.0,
            "retrieval_ms": rag_res["retrieval_ms"],
            "llm_ms": rag_res["llm_ms"],
            "tts_ms": tts_ms,
            "total_ms": total_ms,
        }

        return {
            "query": query,
            "answer": rag_res["answer"],
            "audio_bytes": audio_bytes,
            "audio_format": audio_format,
            "voice": used_voice,
            "sources": rag_res["sources"],
            "latencies": latencies,
            "chunks_count": rag_res["chunks_count"],
            "retrieved_chunks": rag_res["retrieved_chunks"],
        }

    def process_voice(
        self,
        audio_input: Union[str, Path, bytes],
        mime_type: Optional[str] = None,
        return_audio: bool = True,
        top_k: Optional[int] = None,
        voice: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process a voice audio input through full STT -> RAG -> TTS pipeline."""
        t_start = time.perf_counter()

        # 1. Speech-to-Text (STT)
        stt_res = self.stt.transcribe(audio_input, mime_type=mime_type)
        user_query = stt_res["text"]
        stt_ms = stt_res["stt_ms"]

        if not user_query:
            # Handle empty audio or unintelligible speech
            empty_msg = "Sorry, I could not hear any speech clearly. Please try again."
            tts_res = self.tts.synthesize(empty_msg) if return_audio else {"audio_bytes": None, "tts_ms": 0.0, "voice": None, "format": None}
            total_ms = round((time.perf_counter() - t_start) * 1000, 2)
            return {
                "query": "",
                "answer": empty_msg,
                "audio_bytes": tts_res["audio_bytes"],
                "audio_format": tts_res.get("format"),
                "voice": tts_res.get("voice"),
                "sources": [],
                "latencies": {
                    "stt_ms": stt_ms,
                    "retrieval_ms": 0.0,
                    "llm_ms": 0.0,
                    "tts_ms": tts_res["tts_ms"],
                    "total_ms": total_ms,
                },
                "chunks_count": 0,
                "retrieved_chunks": [],
            }

        # 2. RAG Core (Retrieval + LLM Generation)
        rag_res = self.generator.generate(user_query, top_k=top_k)

        # 3. Text-to-Speech (TTS)
        audio_bytes: Optional[bytes] = None
        tts_ms = 0.0
        used_voice = None
        audio_format = None

        if return_audio and rag_res["answer"]:
            tts_res = self.tts.synthesize(rag_res["answer"], voice=voice)
            audio_bytes = tts_res["audio_bytes"]
            tts_ms = tts_res["tts_ms"]
            used_voice = tts_res["voice"]
            audio_format = tts_res["format"]

        total_ms = round((time.perf_counter() - t_start) * 1000, 2)

        latencies = {
            "stt_ms": stt_ms,
            "retrieval_ms": rag_res["retrieval_ms"],
            "llm_ms": rag_res["llm_ms"],
            "tts_ms": tts_ms,
            "total_ms": total_ms,
        }

        return {
            "query": user_query,
            "answer": rag_res["answer"],
            "audio_bytes": audio_bytes,
            "audio_format": audio_format,
            "voice": used_voice,
            "sources": rag_res["sources"],
            "latencies": latencies,
            "chunks_count": rag_res["chunks_count"],
            "retrieved_chunks": rag_res["retrieved_chunks"],
        }


# Global pipeline singleton helper
_pipeline_instance: Optional[VoiceRAGPipeline] = None


def get_pipeline() -> VoiceRAGPipeline:
    """Returns a shared global VoiceRAGPipeline instance."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = VoiceRAGPipeline()
    return _pipeline_instance
