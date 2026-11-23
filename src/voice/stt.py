"""Speech-to-Text (STT) module using Google Gemini Multimodal Audio API.

Transcribes audio from file paths or in-memory byte streams into text with
native support for Arabic, English, and code-switching dialects.
"""

from pathlib import Path
import time
from typing import Any, Dict, Optional, Union
from google import genai
from google.genai import types

from src.config import settings

# Common audio extensions to MIME types
MIME_MAP = {
    ".wav": "audio/wav",
    ".mp3": "audio/mp3",
    ".m4a": "audio/m4a",
    ".ogg": "audio/ogg",
    ".webm": "audio/webm",
    ".aac": "audio/aac",
    ".flac": "audio/flac",
}

STT_TRANSCRIPTION_PROMPT = (
    "Transcribe the spoken audio verbatim in the exact language, dialect, and words spoken. "
    "If the speaker uses a mix of Arabic and English (code-switching), preserve both languages faithfully. "
    "Do NOT translate, summarize, or add quotes. Output ONLY the transcribed text."
)


class GeminiAudioSTT:
    """Transcribes spoken audio using Gemini's native audio understanding API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        self.api_key = api_key or settings.gemini_api_key
        self.model_name = model_name or settings.gemini_model

        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            raise ValueError(
                "GEMINI_API_KEY is missing or invalid. Please configure your key in .env"
            )

        self.client = genai.Client(api_key=self.api_key)

    def transcribe(
        self,
        audio_source: Union[str, Path, bytes],
        mime_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Transcribe an audio file or bytes stream.

        Args:
            audio_source: Path to audio file or raw bytes.
            mime_type: Audio MIME type (e.g. 'audio/wav', 'audio/mp3'). Inferred if path is given.

        Returns:
            Dict containing 'text', 'stt_ms', 'mime_type', and 'size_bytes'.
        """
        # Determine bytes and mime_type
        if isinstance(audio_source, (str, Path)):
            audio_path = Path(audio_source)
            if not audio_path.exists():
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            audio_bytes = audio_path.read_bytes()
            detected_mime = MIME_MAP.get(audio_path.suffix.lower(), "audio/wav")
            target_mime = mime_type or detected_mime
        elif isinstance(audio_source, bytes):
            audio_bytes = audio_source
            target_mime = mime_type or "audio/wav"
        else:
            raise TypeError("audio_source must be a file path (str/Path) or bytes")

        t0 = time.perf_counter()

        audio_part = types.Part.from_bytes(
            data=audio_bytes,
            mime_type=target_mime,
        )

        models_to_try = [self.model_name]
        if "gemini-3.8-flash" not in models_to_try:
            models_to_try.append("gemini-3.8-flash")
        if "gemini-3.5-flash-lite" not in models_to_try:
            models_to_try.append("gemini-3.5-flash-lite")

        response = None
        last_error = None
        for candidate_model in models_to_try:
            for attempt in range(3):
                try:
                    response = self.client.models.generate_content(
                        model=candidate_model,
                        contents=[audio_part, STT_TRANSCRIPTION_PROMPT],
                        config=types.GenerateContentConfig(
                            temperature=0.0,
                        ),
                    )
                    break
                except Exception as exc:
                    last_error = exc
                    time.sleep(1.0 * (attempt + 1))
            if response is not None:
                break

        if response is None:
            raise last_error

        stt_ms = round((time.perf_counter() - t0) * 1000, 2)
        transcribed_text = (response.text or "").strip()

        return {
            "text": transcribed_text,
            "stt_ms": stt_ms,
            "mime_type": target_mime,
            "size_bytes": len(audio_bytes),
        }


# Convenience function
def transcribe_audio(
    audio_source: Union[str, Path, bytes],
    mime_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Helper to instantiate GeminiAudioSTT and transcribe in one call."""
    stt = GeminiAudioSTT()
    return stt.transcribe(audio_source, mime_type=mime_type)
