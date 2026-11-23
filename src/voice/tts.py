"""Text-to-Speech (TTS) module using edge-tts.

Synthesizes voice-ready text into human-like audio using Microsoft Azure Neural voices
with language detection (Egyptian Arabic and English) and low latency in-memory streaming.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import re
import time
from typing import Any, Dict, Optional, Union
import edge_tts

from src.config import settings

# High-quality neural voices
DEFAULT_VOICE_AR = "ar-EG-SalmaNeural"
DEFAULT_VOICE_EN = "en-US-JennyNeural"


def detect_language(text: str) -> str:
    """Detects whether text is primarily Arabic or Latin/English."""
    arabic_chars = len(re.findall(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]", text))
    latin_chars = len(re.findall(r"[a-zA-Z]", text))
    return "ar" if arabic_chars >= latin_chars else "en"


def get_default_voice_for_text(text: str) -> str:
    """Returns the most appropriate neural voice based on language detection."""
    lang = detect_language(text)
    return DEFAULT_VOICE_AR if lang == "ar" else DEFAULT_VOICE_EN


def _run_coroutine_sync(coro):
    """Safely executes an async coroutine from synchronous code."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)


class EdgeTTS:
    """Text-To-Speech synthesizer powered by edge-tts."""

    def __init__(
        self,
        voice_ar: str = DEFAULT_VOICE_AR,
        voice_en: str = DEFAULT_VOICE_EN,
        rate: str = "+0%",
    ):
        self.voice_ar = voice_ar
        self.voice_en = voice_en
        self.rate = rate or settings.tts_rate

    def resolve_voice(self, text: str, requested_voice: Optional[str] = None) -> str:
        """Determines the voice to use, honoring manual override if provided."""
        if requested_voice:
            return requested_voice
        lang = detect_language(text)
        return self.voice_ar if lang == "ar" else self.voice_en

    async def synthesize_bytes_async(
        self,
        text: str,
        voice: Optional[str] = None,
        rate: Optional[str] = None,
    ) -> bytes:
        """Asynchronously converts text into MP3 audio bytes."""
        selected_voice = self.resolve_voice(text, voice)
        selected_rate = rate or self.rate

        communicate = edge_tts.Communicate(text, selected_voice, rate=selected_rate)
        buffer = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buffer.extend(chunk["data"])
        return bytes(buffer)

    async def synthesize_file_async(
        self,
        text: str,
        output_path: Union[str, Path],
        voice: Optional[str] = None,
        rate: Optional[str] = None,
    ) -> Path:
        """Asynchronously converts text and saves it as an MP3 file."""
        selected_voice = self.resolve_voice(text, voice)
        selected_rate = rate or self.rate

        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        communicate = edge_tts.Communicate(text, selected_voice, rate=selected_rate)
        await communicate.save(str(out_path))
        return out_path

    def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        rate: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Synchronously converts text into audio bytes with latency measurement."""
        selected_voice = self.resolve_voice(text, voice)
        t0 = time.perf_counter()

        audio_bytes = _run_coroutine_sync(
            self.synthesize_bytes_async(text, voice=selected_voice, rate=rate)
        )

        tts_ms = round((time.perf_counter() - t0) * 1000, 2)

        return {
            "audio_bytes": audio_bytes,
            "tts_ms": tts_ms,
            "voice": selected_voice,
            "format": "audio/mp3",
            "size_bytes": len(audio_bytes),
        }

    def synthesize_to_file(
        self,
        text: str,
        output_path: Union[str, Path],
        voice: Optional[str] = None,
        rate: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Synchronously converts text and saves to file with latency measurement."""
        selected_voice = self.resolve_voice(text, voice)
        t0 = time.perf_counter()

        file_path = _run_coroutine_sync(
            self.synthesize_file_async(text, output_path, voice=selected_voice, rate=rate)
        )

        tts_ms = round((time.perf_counter() - t0) * 1000, 2)

        return {
            "file_path": str(file_path),
            "tts_ms": tts_ms,
            "voice": selected_voice,
            "format": "audio/mp3",
            "size_bytes": file_path.stat().st_size,
        }


# Convenience helpers
def text_to_speech(
    text: str,
    voice: Optional[str] = None,
    rate: Optional[str] = None,
) -> Dict[str, Any]:
    """Generates speech bytes from text."""
    tts = EdgeTTS()
    return tts.synthesize(text, voice=voice, rate=rate)


def text_to_speech_file(
    text: str,
    output_path: Union[str, Path],
    voice: Optional[str] = None,
    rate: Optional[str] = None,
) -> Dict[str, Any]:
    """Generates speech and saves to an MP3 file."""
    tts = EdgeTTS()
    return tts.synthesize_to_file(text, output_path, voice=voice, rate=rate)
