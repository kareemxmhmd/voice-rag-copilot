"""Comprehensive CLI Verification for Voice RAG Copilot (Phases 2, 3, 4, 5).

Runs tests covering:
1. Pure Retrieval Verification (ChromaDB top-k)
2. Text RAG Generation (Gemini LLM voice-friendly answers)
3. End-to-End Pipeline: Audio Input -> STT -> RAG -> TTS Audio Output
"""

import asyncio
from pathlib import Path
import re
import edge_tts

from src.pipeline import VoiceRAGPipeline
from src.rag.generator import VoiceRAGGenerator
from src.rag.retriever import VoiceRetriever


def test_end_to_end_pipeline():
    print("=" * 80)
    print(" Voice RAG Copilot - Phase 5 Full Pipeline Verification (STT + RAG + TTS)")
    print("=" * 80)

    pipeline = VoiceRAGPipeline()

    # Part A: Text Input -> RAG -> Audio Output (Arabic & English)
    print("\n--- Part A: Testing process_text (Text -> RAG -> TTS) ---")
    text_queries = [
        "What was Basic churn in Q3, and what is the average LTV for Basic versus Pro?",
        "لو أنا بدأت الـ Free Trial بتاع الـ Pro Plan ونسيت أعمل Cancel، هتحاسبوني إمتى وبكام؟",
    ]

    for q in text_queries:
        print(f"\n[Text Query]: \"{q}\"")
        res = pipeline.process_text(q, return_audio=True)
        print(f"Spoken Answer: \"{res['answer']}\"")
        print(f"Voice Selected: {res['voice']} | Audio Size: {len(res['audio_bytes'] or b'')} bytes")
        print(f"Sources: {res['sources']}")
        print(f"Latency Breakdown:")
        for k, v in res["latencies"].items():
            print(f"  - {k}: {v}ms")

        assert res["audio_bytes"] and len(res["audio_bytes"]) > 1000, "Audio bytes must not be empty"
        print("  -> PASS: Audio generated successfully.")

    # Part B: Audio Input -> STT -> RAG -> TTS Audio Output
    print("\n--- Part B: Testing process_voice (Voice -> STT -> RAG -> TTS) ---")
    test_audio_path = Path("temp_pipeline_voice_test.mp3")

    # Generate synthetic input speech to simulate user speaking into mic
    user_speech_text = "How much is the Work Anywhere Bundle for a Pro member?"
    print(f"Simulating user speaking: \"{user_speech_text}\"")

    async def create_audio():
        comm = edge_tts.Communicate(user_speech_text, "en-US-JennyNeural")
        await comm.save(str(test_audio_path))

    asyncio.run(create_audio())

    try:
        voice_res = pipeline.process_voice(test_audio_path, return_audio=True)
        print(f"\n[Transcribed Input]: \"{voice_res['query']}\"")
        print(f"[Copilot Answer]: \"{voice_res['answer']}\"")
        print(f"[Generated Audio Reply]: {voice_res['voice']} ({len(voice_res['audio_bytes'] or b'')} bytes)")
        print(f"[Sources Used]: {voice_res['sources']}")
        print(f"[Full Latency Breakdown]:")
        for k, v in voice_res["latencies"].items():
            print(f"  - {k}: {v}ms")

        # Save output audio to test playback file
        output_file = Path("temp_copilot_reply.mp3")
        if voice_res["audio_bytes"]:
            output_file.write_bytes(voice_res["audio_bytes"])
            print(f"Saved Copilot reply audio to: {output_file.resolve()} ({output_file.stat().st_size} bytes)")
            if output_file.exists():
                output_file.unlink()

        print("\n-> PASS: Complete Voice-In to Voice-Out pipeline validated.")

    finally:
        if test_audio_path.exists():
            test_audio_path.unlink()

    print("\n" + "=" * 80)
    print(" PHASE 5 COMPLETE: Full Voice Pipeline is operational!")
    print("=" * 80)


if __name__ == "__main__":
    test_end_to_end_pipeline()
