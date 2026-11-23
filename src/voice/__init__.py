"""Voice modules for Voice RAG Copilot (STT and TTS)."""

from src.voice.stt import GeminiAudioSTT, transcribe_audio
from src.voice.tts import EdgeTTS, detect_language, text_to_speech, text_to_speech_file

__all__ = [
    "GeminiAudioSTT",
    "transcribe_audio",
    "EdgeTTS",
    "detect_language",
    "text_to_speech",
    "text_to_speech_file",
]
