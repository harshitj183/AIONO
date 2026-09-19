"""
Document Search Tool – RAG over internal business documents.

Uses TF-IDF style weighted scoring for semantic-like retrieval.
No heavy ML dependencies (faiss/sentence-transformers removed for cloud deployment).
Falls back to pure keyword search if needed.

Why TF-IDF instead of FAISS:
- faiss-cpu + sentence-transformers = ~400MB RAM — exceeds free-tier 512MB limit
- TF-IDF gives good recall for business document search with <50 documents
- Zero cold-start time (no model download)
"""

import json
import sqlite3
import math
import re
from typing import Optional
from langchain_core.tools import tool
from app.config import settings


def _get_db_path() -> str:
    return settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")


def _load_docs_from_db() -> list[dict]:
    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT id, title, doc_type, department, content, tags, author, published_at FROM documents"
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def _tokenize(text: str) -> list[str]:
    """Lowercase, strip punctuation, split into tokens."""
    return re.findall(r"[a-z0-9]+", text.lower())


def _tfidf_score(query: str, doc: dict, all_docs: list[dict]) -> float:
    """
    Compute a TF-IDF-like relevance score between query and document.
    Higher = more relevant.
    """
    full_text = f"{doc['title']} {doc['title']} {doc['content']} {doc.get('tags','')}"
    doc_tokens = _tokenize(full_text)
    query_tokens = _tokenize(query)

    if not doc_tokens or not query_tokens:
        return 0.0

    doc_token_count = len(doc_tokens)
    doc_freq = {}
    for tok in doc_tokens:
        doc_freq[tok] = doc_freq.get(tok, 0) + 1

    N = len(all_docs)
    score = 0.0

    for qt in query_tokens:
        # TF: frequency of query term in document (normalized)
        tf = doc_freq.get(qt, 0) / doc_token_count

        # IDF: how rare is this term across all documents
        docs_with_term = sum(
            1 for d in all_docs
            if qt in _tokenize(f"{d['title']} {d['content']} {d.get('tags','')}")
        )
        idf = math.log((N + 1) / (docs_with_term + 1)) + 1.0

        score += tf * idf

    # Boost if query terms appear in title or tags
    title_tags = _tokenize(f"{doc['title']} {doc.get('tags','')}")
    title_hits = sum(1 for qt in query_tokens if qt in title_tags)
    score += title_hits * 0.3

    return round(score, 4)


@tool
def document_search_tool(query: str, top_k: int = 3, doc_type: Optional[str] = None) -> str:
    """
    Search internal business documents using TF-IDF relevance scoring.

    Searches across:
    - Release notes (product updates, version changes)
    - Incident reports (outages, regressions, root cause analyses)
    - Policy documents (SLAs, escalation procedures)
    - Sales and HR memos (quarterly reviews, attrition analysis)
    - Product roadmaps

    Args:
        query: Natural language search query (e.g. "authentication failures Product X login")
        top_k: Number of documents to return (default 3, max 5)
        doc_type: Optional filter — release_note | incident_report | policy | memo

    Returns JSON with matching documents including title, snippet, relevance score,
    doc_type, department, author, and published date.
    """
    try:
        top_k = min(top_k, 5)
        docs = _load_docs_from_db()

        if not docs:
            return json.dumps({"error": "No documents found in the database.", "results": []})

        # Apply doc_type filter
        filtered = [d for d in docs if d.get("doc_type") == doc_type] if doc_type else docs
        if doc_type and not filtered:
            return json.dumps({"error": f"No documents of type '{doc_type}' found.", "results": []})

        # Score all docs
        scored = []
        for doc in filtered:
            score = _tfidf_score(query, doc, filtered)
            if score > 0:
                scored.append((score, doc))

        # Sort by relevance
        scored.sort(key=lambda x: x[0], reverse=True)
        top_docs = scored[:top_k]

        # If nothing matched, return top_k by recency
        if not top_docs:
            top_docs = [(0.0, d) for d in filtered[:top_k]]

        results = []
        for score, doc in top_docs:
            snippet = doc["content"][:400] + "..." if len(doc["content"]) > 400 else doc["content"]
            results.append({
                "id": doc["id"],
                "title": doc["title"],
                "doc_type": doc["doc_type"],
                "department": doc["department"],
                "author": doc["author"],
                "published_at": doc["published_at"],
                "relevance_score": score,
                "snippet": snippet,
                "tags": doc.get("tags", ""),
            })

        return json.dumps({
            "query": query,
            "results": results,
            "total_docs_searched": len(filtered),
            "search_type": "tfidf",
        })

    except Exception as e:
        return json.dumps({"error": f"Document search failed: {str(e)}", "query": query, "results": []})
