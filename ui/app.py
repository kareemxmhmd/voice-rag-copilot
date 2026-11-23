"""Streamlit Frontend Application for NovaCart Voice RAG Copilot.

Provides an interactive web dashboard for voice and text querying with live
microphone recording (st.audio_input), audio playback, latency metrics breakdown,
and knowledge base source inspection.
"""

import sys
from pathlib import Path

# Add project root to sys.path so imports work from within ui/ directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from src.config import settings
from src.pipeline import get_pipeline

st.set_page_config(
    page_title="NovaCart Voice RAG Copilot",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E88E5;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #555;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 12px;
        border-left: 4px solid #1E88E5;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_cached_pipeline():
    """Cache the pipeline so it initializes only once across Streamlit reruns."""
    return get_pipeline()


pipeline = get_cached_pipeline()

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/microphone.png", width=110)
    st.markdown("### System Controls")

    top_k = st.slider("Top-K Context Chunks", min_value=1, max_value=6, value=3)

    voice_option = st.selectbox(
        "TTS Voice Mode",
        options=[
            "Auto (Detect Language)",
            "Egyptian Arabic (Salma)",
            "Egyptian Arabic (Shakir)",
            "US English (Jenny)",
            "US English (Guy)",
        ],
        index=0,
    )

    voice_map = {
        "Auto (Detect Language)": None,
        "Egyptian Arabic (Salma)": "ar-EG-SalmaNeural",
        "Egyptian Arabic (Shakir)": "ar-EG-ShakirNeural",
        "US English (Jenny)": "en-US-JennyNeural",
        "US English (Guy)": "en-US-GuyNeural",
    }
    selected_voice = voice_map[voice_option]

    st.markdown("---")
    st.markdown("### Knowledge Base Status")
    try:
        count = pipeline.generator.retriever.collection.count()
        st.success(f"Indexed Chunks: **{count}**")
        st.caption(f"Collection: `{settings.collection_name}`")
        st.caption(f"LLM: `{settings.gemini_model}`")
        st.caption(f"Embedding: `{settings.embedding_model}`")
    except Exception as e:
        st.warning(f"Vector store error: {e}")

    st.markdown("---")
    st.markdown("### Quick Sample Queries")
    samples = [
        "How much is the Work Anywhere Bundle for a Pro member?",
        "لو أنا بدأت الـ Free Trial بتاع الـ Pro Plan ونسيت أعمل Cancel هتحاسبوني بكام؟",
        "What was Basic churn in Q3, and what is the average LTV?",
        "اشتريت سماعة NovaBuds Pro وطلعت Defective ينفع أرجعها؟",
    ]
    for s in samples:
        if st.button(s, key=f"btn_{s[:20]}"):
            st.session_state["sample_text"] = s

# --- MAIN PAGE ---
st.markdown('<div class="main-header"> NovaCart Voice RAG Copilot</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Low-Latency Bilingual AI Assistant for E-Commerce & Subscription Operations</div>',
    unsafe_allow_html=True,
)

tab_voice, tab_text = st.tabs(["Voice Input (Microphone & File)", "Text Input"])

result_data = None

# TAB 1: VOICE INPUT
with tab_voice:
    st.markdown("#### Speak your question:")
    col_mic, col_file = st.columns([1, 1])

    with col_mic:
        st.markdown("**Option 1: Record from Microphone**")
        audio_mic = st.audio_input("Click to record and ask:")

    with col_file:
        st.markdown("**Option 2: Upload Audio File**")
        audio_file = st.file_uploader(
            "Upload WAV, MP3, WebM, or OGG",
            type=["wav", "mp3", "m4a", "ogg", "webm"],
        )

    active_audio = audio_mic or audio_file

    if active_audio is not None:
        if st.button("Process Voice Query", key="btn_run_voice", type="primary"):
            with st.spinner("Transcribing audio and retrieving answers..."):
                audio_bytes = active_audio.read()
                mime = active_audio.type or "audio/wav"
                result_data = pipeline.process_voice(
                    audio_input=audio_bytes,
                    mime_type=mime,
                    return_audio=True,
                    top_k=top_k,
                    voice=selected_voice,
                )

# TAB 2: TEXT INPUT
with tab_text:
    st.markdown("#### Type your question:")
    default_text = st.session_state.get("sample_text", "")
    user_text = st.text_input(
        "Ask about policies, plans, churn reports, or catalog:",
        value=default_text,
        placeholder="e.g. How do Pro subscription refund rules work?",
    )

    if st.button("Ask Copilot", key="btn_run_text", type="primary"):
        if user_text.strip():
            with st.spinner("Consulting knowledge base..."):
                result_data = pipeline.process_text(
                    query=user_text.strip(),
                    return_audio=True,
                    top_k=top_k,
                    voice=selected_voice,
                )
        else:
            st.warning("Please type a question first.")

# --- DISPLAY RESULTS ---
if result_data:
    st.markdown("---")
    st.markdown("### Copilot Response")

    # 1. Spoken Audio Player
    if result_data.get("audio_bytes"):
        st.markdown("#### Audio Reply:")
        st.audio(result_data["audio_bytes"], format="audio/mp3", autoplay=True)

    # 2. Transcribed query & Answer text
    col_q, col_a = st.columns(2)
    with col_q:
        st.markdown("**User Query:**")
        st.info(result_data["query"] or "(Empty query)")

    with col_a:
        st.markdown("**Voice Answer:**")
        st.success(result_data["answer"])

    # 3. Latency Dashboard Metrics
    st.markdown("#### Latency Observability Breakdown")
    lat = result_data["latencies"]
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("STT (Transcribe)", f"{lat['stt_ms']:.0f} ms")
    with c2:
        st.metric("Retrieval (Vector)", f"{lat['retrieval_ms']:.0f} ms")
    with c3:
        st.metric("LLM (Generation)", f"{lat['llm_ms']:.0f} ms")
    with c4:
        st.metric("TTS (Speech)", f"{lat['tts_ms']:.0f} ms")
    with c5:
        st.metric("Total Latency", f"{lat['total_ms'] / 1000:.2f} s")

    # 4. Source Citations
    with st.expander(f"Ground Truth Sources & Citations ({len(result_data['sources'])} files)"):
        st.markdown(f"**Referenced Documents:** `{', '.join(result_data['sources'])}`")
        st.markdown("---")
        for idx, chunk in enumerate(result_data.get("retrieved_chunks", []), 1):
            st.markdown(
                f"**#{idx} [{chunk.get('source')}]** — *{chunk.get('section', '')} > {chunk.get('subsection', '')}* (Cosine Similarity: `{chunk.get('score', 0):.4f}`)"
            )
            st.code(chunk.get("content", ""), language="markdown")
