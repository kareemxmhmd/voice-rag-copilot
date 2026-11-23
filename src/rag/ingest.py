"""Ingestion module for Voice RAG Copilot.

Reads markdown knowledge base files, extracts sections with header hierarchy,
generates embeddings via Gemini API (text-embedding-004), and stores them in ChromaDB.
"""

from dataclasses import dataclass
from pathlib import Path
import re
import time
from typing import Any, Dict, List, Optional
import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from google import genai

from src.config import resolve_api_key, settings


@dataclass
class DocumentChunk:
    """Represents a structured knowledge chunk with metadata."""

    chunk_id: str
    content: str
    source_file: str
    doc_title: str
    section: str
    subsection: str
    chunk_index: int

    def to_metadata(self) -> Dict[str, Any]:
        return {
            "source": self.source_file,
            "doc_title": self.doc_title,
            "section": self.section,
            "subsection": self.subsection,
            "chunk_index": self.chunk_index,
        }


def parse_markdown_to_chunks(
    file_path: Path, max_chunk_chars: int = 1200
) -> List[DocumentChunk]:
    """Parse a markdown file into hierarchical section-based chunks."""
    text = file_path.read_text(encoding="utf-8")
    filename = file_path.name
    lines = text.splitlines()

    doc_title = filename.replace(".md", "").replace("_", " ").title()
    current_section = "Overview"
    current_subsection = ""

    # Find top document title from first # header if present
    for line in lines:
        if line.startswith("# "):
            doc_title = line.replace("# ", "").strip()
            break

    sections: List[Dict[str, Any]] = []
    buffer: List[str] = []

    def flush_section():
        nonlocal buffer, current_section, current_subsection
        content = "\n".join(buffer).strip()
        if content:
            sections.append(
                {
                    "section": current_section,
                    "subsection": current_subsection,
                    "content": content,
                }
            )
        buffer = []

    for line in lines:
        if line.startswith("# ") and not line.startswith("## "):
            continue

        if line.startswith("## "):
            flush_section()
            current_section = line.replace("## ", "").strip()
            current_subsection = ""
            continue

        if line.startswith("### "):
            flush_section()
            current_subsection = line.replace("### ", "").strip()
            continue

        buffer.append(line)

    flush_section()

    chunks: List[DocumentChunk] = []
    chunk_counter = 0

    for sec in sections:
        sec_name = sec["section"]
        sub_name = sec["subsection"]
        content = sec["content"]

        paragraphs = re.split(r"\n\s*\n", content)
        current_block: List[str] = []
        current_len = 0

        for p in paragraphs:
            p_str = p.strip()
            if not p_str:
                continue

            if current_len + len(p_str) > max_chunk_chars and current_block:
                block_text = "\n\n".join(current_block).strip()
                header_context = f"[Document: {doc_title}]\n[Section: {sec_name}"
                if sub_name:
                    header_context += f" > {sub_name}"
                header_context += "]\n\n"

                full_chunk_text = header_context + block_text
                chunk_id = f"{file_path.stem}_chunk_{chunk_counter}"

                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        content=full_chunk_text,
                        source_file=filename,
                        doc_title=doc_title,
                        section=sec_name,
                        subsection=sub_name,
                        chunk_index=chunk_counter,
                    )
                )
                chunk_counter += 1
                current_block = [p_str]
                current_len = len(p_str)
            else:
                current_block.append(p_str)
                current_len += len(p_str)

        if current_block:
            block_text = "\n\n".join(current_block).strip()
            header_context = f"[Document: {doc_title}]\n[Section: {sec_name}"
            if sub_name:
                header_context += f" > {sub_name}"
            header_context += "]\n\n"

            full_chunk_text = header_context + block_text
            chunk_id = f"{file_path.stem}_chunk_{chunk_counter}"

            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    content=full_chunk_text,
                    source_file=filename,
                    doc_title=doc_title,
                    section=sec_name,
                    subsection=sub_name,
                    chunk_index=chunk_counter,
                )
            )
            chunk_counter += 1

    return chunks


class GeminiEmbeddingFunction(EmbeddingFunction):
    """Custom ChromaDB Embedding Function using Google Gemini text-embedding-004 API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or settings.gemini_api_key or resolve_api_key()
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            raise ValueError(
                "GEMINI_API_KEY is missing or invalid. Please configure your key in .env or Streamlit secrets."
            )
        target_model = model or settings.embedding_model
        if not target_model.startswith("models/"):
            target_model = f"models/{target_model}"
        self.model = target_model
        self._client = genai.Client(api_key=self.api_key)

    def __call__(self, input: Documents) -> Embeddings:
        embeddings: Embeddings = []
        batch_size = 20

        for i in range(0, len(input), batch_size):
            batch = list(input[i : i + batch_size])
            for attempt in range(3):
                try:
                    resp = self._client.models.embed_content(
                        model=self.model,
                        contents=batch,
                    )
                    if resp.embeddings:
                        for item in resp.embeddings:
                            embeddings.append(item.values)
                    break
                except Exception as exc:
                    if attempt == 2:
                        raise exc
                    time.sleep(1.0 * (attempt + 1))

        return embeddings


def get_embedding_function() -> EmbeddingFunction:
    """Return configured Gemini embedding function."""
    return GeminiEmbeddingFunction(
        api_key=settings.gemini_api_key,
        model=settings.embedding_model,
    )


def ingest_knowledge_base(
    raw_dir: Optional[Path] = None,
    persist_dir: Optional[Path] = None,
    collection_name: Optional[str] = None,
) -> int:
    """Ingests all markdown documents in raw_dir into ChromaDB using Gemini API."""
    target_raw_dir = raw_dir or settings.raw_data_dir
    target_persist_dir = persist_dir or settings.vector_store_dir
    target_collection = collection_name or settings.collection_name

    target_persist_dir.mkdir(parents=True, exist_ok=True)

    print(f"--> Ingestion source: {target_raw_dir}")
    print(f"--> ChromaDB persist path: {target_persist_dir}")
    print(f"--> Collection: {target_collection}")
    print(f"--> Embedding Model: {settings.embedding_model} (Gemini API)")

    embedding_fn = get_embedding_function()
    client = chromadb.PersistentClient(path=str(target_persist_dir))

    # Recreate collection cleanly
    try:
        client.delete_collection(target_collection)
    except Exception:
        pass

    collection = client.create_collection(
        name=target_collection,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )

    all_chunks: List[DocumentChunk] = []
    md_files = sorted(list(target_raw_dir.glob("*.md")))

    if not md_files:
        print(f"[Warning] No markdown files found in {target_raw_dir}")
        return 0

    for md_file in md_files:
        chunks = parse_markdown_to_chunks(md_file, max_chunk_chars=1200)
        print(f"  Processed {md_file.name}: {len(chunks)} chunks")
        all_chunks.extend(chunks)

    if all_chunks:
        ids = [c.chunk_id for c in all_chunks]
        documents = [c.content for c in all_chunks]
        metadatas = [c.to_metadata() for c in all_chunks]

        batch_size = 20
        for i in range(0, len(all_chunks), batch_size):
            print(f"  Embedding batch {i // batch_size + 1}/{(len(all_chunks) + batch_size - 1) // batch_size}...")
            collection.add(
                ids=ids[i : i + batch_size],
                documents=documents[i : i + batch_size],
                metadatas=metadatas[i : i + batch_size],
            )

    stored_count = collection.count()
    print(f"--> Successfully indexed {stored_count} chunks into '{target_collection}'")
    return stored_count


if __name__ == "__main__":
    count = ingest_knowledge_base()
    print(f"Ingestion completed. Total chunks: {count}")
