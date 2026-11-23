"""Voice modules for Voice RAG Copilot."""

from src.voice.stt import GeminiAudioSTT, transcribe_audio

__all__ = ["GeminiAudioSTT", "transcribe_audio"]
