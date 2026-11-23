"""Voice RAG Generator module.

Combines the vector retriever and Gemini LLM to generate strictly grounded,
conversational spoken-style answers with per-stage latency tracking.
"""

from pathlib import Path
import re
import time
from typing import Any, Dict, List, Optional
from google import genai
from google.genai import types

from src.config import settings
from src.rag.prompts import VOICE_SYSTEM_PROMPT, build_rag_prompt
from src.rag.retriever import VoiceRetriever


def sanitize_for_speech(text: str) -> str:
    """Removes all markdown formatting to make text clean for TTS."""
    # Remove markdown headers (#, ##, etc.)
    cleaned = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    # Remove bullet markers (*, -, +, •)
    cleaned = re.sub(r"^\s*[\*\-\+•]\s+", "", cleaned, flags=re.MULTILINE)
    # Remove bold, italics, code, strikethrough: *, **, _, __, `, ~
    cleaned = re.sub(r"[\*\_`~]", "", cleaned)
    # Remove markdown links: [text](url) -> text
    cleaned = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", cleaned)
    # Remove brackets
    cleaned = re.sub(r"[\[\]]", "", cleaned)
    # Collapse multiple whitespaces/newlines into smooth speech pauses
    cleaned = re.sub(r"\n+", " ", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip()


class VoiceRAGGenerator:
    """Generates voice-ready answers using retrieved context and Gemini LLM."""

    def __init__(
        self,
        retriever: Optional[VoiceRetriever] = None,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.retriever = retriever or VoiceRetriever()
        self.model_name = model_name or settings.gemini_model
        self.api_key = api_key or settings.api_key or settings.gemini_api_key

        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            raise ValueError(
                "GEMINI_API_KEY is missing or invalid. Please configure your key in .env"
            )

        self.client = genai.Client(api_key=self.api_key)

    def generate(
        self,
        query: str,
        top_k: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Runs the complete Retrieval + Generation pipeline with latency timing."""
        # 1. Retrieval stage
        t0 = time.perf_counter()
        retrieved_chunks = self.retriever.retrieve(query, top_k=top_k)
        t_retrieval = time.perf_counter()
        retrieval_ms = round((t_retrieval - t0) * 1000, 2)

        context_texts = [c["content"] for c in retrieved_chunks]
        sources = list(dict.fromkeys(c["source"] for c in retrieved_chunks))

        # 2. Generation stage
        prompt = build_rag_prompt(query, context_texts)
        gen_config = types.GenerateContentConfig(
            system_instruction=VOICE_SYSTEM_PROMPT,
            temperature=0.2,
        )

        response = None
        models_to_try = [self.model_name]
        if "gemini-3.8-flash" not in models_to_try:
            models_to_try.append("gemini-3.8-flash")
        if "gemini-3.5-flash-lite" not in models_to_try:
            models_to_try.append("gemini-3.5-flash-lite")

        last_error = None
        for candidate_model in models_to_try:
            for attempt in range(3):
                try:
                    response = self.client.models.generate_content(
                        model=candidate_model,
                        contents=prompt,
                        config=gen_config,
                    )
                    break
                except Exception as exc:
                    last_error = exc
                    time.sleep(1.0 * (attempt + 1))
            if response is not None:
                break

        if response is None:
            raise last_error

        t_llm = time.perf_counter()
        llm_ms = round((t_llm - t_retrieval) * 1000, 2)
        total_ms = round((t_llm - t0) * 1000, 2)

        raw_answer = response.text or ""
        clean_answer = sanitize_for_speech(raw_answer)

        return {
            "query": query,
            "answer": clean_answer,
            "raw_answer": raw_answer,
            "sources": sources,
            "retrieval_ms": retrieval_ms,
            "llm_ms": llm_ms,
            "total_ms": total_ms,
            "chunks_count": len(retrieved_chunks),
            "retrieved_chunks": retrieved_chunks,
        }


# Convenience function
def generate_voice_answer(query: str, top_k: Optional[int] = None) -> Dict[str, Any]:
    """Helper function to execute retrieval + generation directly."""
    generator = VoiceRAGGenerator()
    return generator.generate(query, top_k=top_k)
