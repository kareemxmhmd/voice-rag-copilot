"""Retriever module for Voice RAG Copilot.

Queries ChromaDB vector store and retrieves the top-k most relevant chunks
with similarity scores and source metadata.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import chromadb

from src.config import settings
from src.rag.ingest import get_embedding_function


class VoiceRetriever:
    """Retrieves context chunks from persistent ChromaDB index."""

    def __init__(
        self,
        persist_dir: Optional[Path] = None,
        collection_name: Optional[str] = None,
        top_k: Optional[int] = None,
    ):
        self.persist_dir = persist_dir or settings.vector_store_dir
        self.collection_name = collection_name or settings.collection_name
        self.top_k = top_k or settings.top_k

        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        self.embedding_fn = get_embedding_function()
        self.collection = self.client.get_collection(
            name=self.collection_name,
            embedding_function=self.embedding_fn,
        )

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Query vector store and return top_k chunks with metadata and similarity score."""
        k = top_k or self.top_k
        results = self.collection.query(
            query_texts=[query],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )

        retrieved: List[Dict[str, Any]] = []

        if not results or not results["documents"] or not results["documents"][0]:
            return retrieved

        docs = results["documents"][0]
        metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
        distances = (
            results["distances"][0] if results.get("distances") else [0.0] * len(docs)
        )
        ids = results["ids"][0] if results.get("ids") else [""] * len(docs)

        for chunk_id, doc, meta, dist in zip(ids, docs, metas, distances):
            # Chroma with cosine distance: distance is 1 - cosine_similarity
            # For cosine distance: score = 1.0 - distance
            similarity_score = round(max(0.0, 1.0 - float(dist)), 4)

            retrieved.append(
                {
                    "id": chunk_id,
                    "content": doc,
                    "source": meta.get("source", "unknown"),
                    "doc_title": meta.get("doc_title", ""),
                    "section": meta.get("section", ""),
                    "subsection": meta.get("subsection", ""),
                    "score": similarity_score,
                    "distance": round(float(dist), 4),
                    "metadata": meta,
                }
            )

        return retrieved


# Convenience function
def retrieve_context(query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
    """Convenience helper to retrieve context directly."""
    retriever = VoiceRetriever(top_k=top_k)
    return retriever.retrieve(query, top_k=top_k)
