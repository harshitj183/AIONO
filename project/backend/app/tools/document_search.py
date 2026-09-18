"""
Document Search Tool – RAG over internal business documents.
Uses sentence-transformers for embeddings + FAISS for vector search.
Falls back to keyword search if the vector index is not ready.
"""

import json
import sqlite3
import os
from typing import Optional
from langchain_core.tools import tool
from app.config import settings

# Optional FAISS – gracefully degrade to keyword search if unavailable
try:
    import faiss
    import numpy as np
    from sentence_transformers import SentenceTransformer
    _FAISS_AVAILABLE = True
except ImportError:
    _FAISS_AVAILABLE = False

_index = None
_doc_store: list[dict] = []
_embedder = None
_INDEX_PATH = "aiono_docs.faiss"


def _get_db_path() -> str:
    return settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")


def _load_docs_from_db() -> list[dict]:
    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, title, doc_type, department, content, tags, author, published_at FROM documents")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def _build_index(docs: list[dict]):
    """Build a FAISS index over document content."""
    global _index, _doc_store, _embedder
    if not _FAISS_AVAILABLE:
        return
    _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    texts = [f"{d['title']}. {d['content']}" for d in docs]
    embeddings = _embedder.encode(texts, show_progress_bar=False).astype("float32")
    faiss.normalize_L2(embeddings)
    _index = faiss.IndexFlatIP(embeddings.shape[1])
    _index.add(embeddings)
    _doc_store = docs


def _ensure_index():
    global _index, _doc_store
    if _index is None or len(_doc_store) == 0:
        docs = _load_docs_from_db()
        if docs:
            _build_index(docs)


def _keyword_search(query: str, docs: list[dict], top_k: int = 3) -> list[dict]:
    """Simple keyword fallback search."""
    q_lower = query.lower()
    scored = []
    for doc in docs:
        text = f"{doc['title']} {doc['content']} {doc.get('tags', '')}".lower()
        score = sum(1 for word in q_lower.split() if word in text)
        if score > 0:
            scored.append((score, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [d for _, d in scored[:top_k]]


@tool
def document_search_tool(query: str, top_k: int = 3, doc_type: Optional[str] = None) -> str:
    """
    Search internal business documents using semantic similarity.

    This tool searches through:
    - Release notes
    - Incident reports
    - Policy documents
    - Sales and HR memos
    - Product roadmaps

    Args:
        query: Natural language search query (e.g. "authentication issues Product X")
        top_k: Number of documents to return (default 3, max 5)
        doc_type: Optional filter by type: release_note | incident_report | policy | memo

    Returns a JSON array of matching documents with title, content snippet, relevance score,
    doc_type, department, author, and published date.
    """
    try:
        top_k = min(top_k, 5)
        docs = _load_docs_from_db()
        if not docs:
            return json.dumps({"error": "No documents found in the database."})

        # Apply doc_type filter if requested
        if doc_type:
            docs = [d for d in docs if d.get("doc_type") == doc_type]
            if not docs:
                return json.dumps({"error": f"No documents found with type '{doc_type}'."})

        # Try FAISS vector search
        if _FAISS_AVAILABLE:
            _ensure_index()
            if _index is not None and _embedder is not None:
                q_emb = _embedder.encode([query]).astype("float32")
                faiss.normalize_L2(q_emb)
                scores, indices = _index.search(q_emb, min(top_k, len(_doc_store)))
                results = []
                for score, idx in zip(scores[0], indices[0]):
                    if idx < 0:
                        continue
                    doc = _doc_store[idx]
                    # Apply doc_type filter on vector results too
                    if doc_type and doc.get("doc_type") != doc_type:
                        continue
                    snippet = doc["content"][:400] + "..." if len(doc["content"]) > 400 else doc["content"]
                    results.append({
                        "id": doc["id"],
                        "title": doc["title"],
                        "doc_type": doc["doc_type"],
                        "department": doc["department"],
                        "author": doc["author"],
                        "published_at": doc["published_at"],
                        "relevance_score": round(float(score), 3),
                        "snippet": snippet,
                        "tags": doc.get("tags", ""),
                    })
                return json.dumps({"query": query, "results": results,
                                   "search_type": "semantic"})

        # Fallback: keyword search
        matched = _keyword_search(query, docs, top_k)
        results = []
        for doc in matched:
            snippet = doc["content"][:400] + "..." if len(doc["content"]) > 400 else doc["content"]
            results.append({
                "id": doc["id"],
                "title": doc["title"],
                "doc_type": doc["doc_type"],
                "department": doc["department"],
                "author": doc["author"],
                "published_at": doc["published_at"],
                "relevance_score": None,
                "snippet": snippet,
                "tags": doc.get("tags", ""),
            })
        return json.dumps({"query": query, "results": results, "search_type": "keyword"})

    except Exception as e:
        return json.dumps({"error": f"Document search failed: {str(e)}", "query": query})
