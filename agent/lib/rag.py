"""
RAG layer for persona workflow. Producer agents index; curate retrieves.
Uses Qdrant. All data scoped by run_id for strict session isolation.
"""

import json
import os
import uuid
from typing import Any

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
RAG_TOP_K = int(os.environ.get("RAG_TOP_K", "20"))
RAG_TOP_K_PER_QUERY = int(os.environ.get("RAG_TOP_K_PER_QUERY", "8"))
RAG_CHUNK_MAX_CHARS = int(os.environ.get("RAG_CHUNK_MAX_CHARS", "1500"))
RAG_CHUNK_OVERLAP = int(os.environ.get("RAG_CHUNK_OVERLAP", "100"))
OPENAI_EMBEDDING_MODEL = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
COLLECTION_NAME = "persona_chunks"
VECTOR_SIZE = 1536


def _get_client():
    from qdrant_client import QdrantClient
    return QdrantClient(url=QDRANT_URL, prefer_grpc=False, check_compatibility=False)


def _ensure_collection(client):
    from qdrant_client.http import models as qdrant_models
    collections = client.get_collections().collections
    names = [c.name for c in collections]
    if COLLECTION_NAME not in names:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=qdrant_models.VectorParams(size=VECTOR_SIZE, distance=qdrant_models.Distance.COSINE),
        )


def embed(text: str) -> list[float]:
    """Call OpenAI embeddings API. Returns 1536-dim vector for text-embedding-3-small."""
    import requests
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")
    resp = requests.post(
        "https://api.openai.com/v1/embeddings",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": OPENAI_EMBEDDING_MODEL, "input": text[:8000]},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["data"][0]["embedding"]


def chunk_contents(contents_obj: dict) -> list[dict[str, Any]]:
    """
    Chunk contents for indexing. contents_obj is {urls: [...], contents: {url: {text, summary, highlights}}}.
    Returns list of {url, chunk_index, chunk_text, metadata}.
    """
    chunks: list[dict[str, Any]] = []
    inner = contents_obj.get("contents", contents_obj)
    if not isinstance(inner, dict):
        return chunks
    for url, data in inner.items():
        if not isinstance(data, dict):
            continue
        idx = 0
        summary = (data.get("summary") or "").strip()
        if summary:
            chunks.append({
                "url": url,
                "chunk_index": idx,
                "chunk_text": summary,
                "metadata": {"source": "summary"},
            })
            idx += 1
        for h in data.get("highlights") or []:
            t = (h if isinstance(h, str) else str(h))[:4000].strip()
            if t:
                chunks.append({
                    "url": url,
                    "chunk_index": idx,
                    "chunk_text": t,
                    "metadata": {"source": "highlights"},
                })
                idx += 1
        text = (data.get("text") or "").strip()
        if text:
            start = 0
            while start < len(text):
                end = start + RAG_CHUNK_MAX_CHARS
                chunk = text[start:end]
                if chunk.strip():
                    chunks.append({
                        "url": url,
                        "chunk_index": idx,
                        "chunk_text": chunk,
                        "metadata": {"source": "text"},
                    })
                    idx += 1
                start = end - RAG_CHUNK_OVERLAP
    return chunks


def chunk_research(research: dict) -> list[dict[str, Any]]:
    """Chunk key research fields for indexing."""
    chunks: list[dict[str, Any]] = []
    idx = 0
    for key in ("full_name", "bio", "mission_statement", "specialization"):
        v = research.get(key)
        if v and isinstance(v, str):
            chunks.append({
                "url": "",
                "chunk_index": idx,
                "chunk_text": v.strip(),
                "metadata": {"source": "research", "field": key},
            })
            idx += 1
    for key in ("skills", "focus_areas", "values", "domain_expertise"):
        arr = research.get(key) or []
        if isinstance(arr, list) and arr:
            text = " ".join(str(x) for x in arr[:20])
            if text.strip():
                chunks.append({
                    "url": "",
                    "chunk_index": idx,
                    "chunk_text": text.strip(),
                    "metadata": {"source": "research", "field": key},
                })
                idx += 1
    projects = research.get("projects") or []
    if isinstance(projects, list):
        for p in projects[:10]:
            if isinstance(p, dict):
                parts = []
                for k in ("name", "description", "outcome"):
                    if p.get(k):
                        parts.append(str(p[k]))
                if parts:
                    chunks.append({
                        "url": p.get("url") or "",
                        "chunk_index": idx,
                        "chunk_text": " | ".join(parts)[:2000],
                        "metadata": {"source": "research", "field": "projects"},
                    })
                    idx += 1
    return chunks


def index_chunks(run_id: str, chunks: list[dict[str, Any]]) -> int:
    """Embed and upsert chunks into Qdrant. Returns count indexed."""
    if not chunks:
        return 0
    from qdrant_client.http import models as qdrant_models
    client = _get_client()
    _ensure_collection(client)
    points = []
    for c in chunks:
        vec = embed(c["chunk_text"])
        payload = {
            "run_id": run_id,
            "url": c.get("url", ""),
            "chunk_index": c.get("chunk_index", 0),
            "chunk_text": c["chunk_text"],
            "metadata": c.get("metadata", {}),
        }
        points.append(qdrant_models.PointStruct(
            id=str(uuid.uuid4()),
            vector=vec,
            payload=payload,
        ))
    client.upsert(collection_name=COLLECTION_NAME, points=points, wait=True)
    return len(chunks)


def build_queries(research: dict) -> list[str]:
    """Build query strings from research for multi-query retrieval."""
    queries = []
    name = research.get("full_name") or ""
    bio = (research.get("bio") or "")[:500]
    if name or bio:
        queries.append(f"{name} {bio}".strip())
    skills = research.get("skills") or []
    focus = research.get("focus_areas") or []
    spec = research.get("specialization") or ""
    if skills or focus or spec:
        queries.append(" ".join(
            [spec] + [str(x) for x in (skills[:10] + focus[:5])]
        ).strip())
    projects = research.get("projects") or []
    if isinstance(projects, list) and projects:
        names = [p.get("name") for p in projects[:5] if isinstance(p, dict) and p.get("name")]
        if names:
            queries.append(" ".join(names))
    return [q for q in queries if q]


def retrieve(run_id: str, queries: list[str], top_k: int = RAG_TOP_K) -> list[dict[str, Any]]:
    """
    Multi-query retrieval. Returns list of {chunk_text, url, metadata}.
    Filters by run_id. Dedupes by (url, chunk_index).
    """
    if not queries:
        return []
    from qdrant_client.http import models as qdrant_models
    client = _get_client()
    seen: set[tuple[str, int]] = set()
    results: list[dict[str, Any]] = []
    k_per = min(RAG_TOP_K_PER_QUERY, max(1, top_k // len(queries)))
    for q in queries:
        q_vec = embed(q)
        resp = client.query_points(
            collection_name=COLLECTION_NAME,
            query=q_vec,
            query_filter=qdrant_models.Filter(
                must=[qdrant_models.FieldCondition(key="run_id", match=qdrant_models.MatchValue(value=run_id))]
            ),
            limit=k_per,
            with_payload=True,
        )
        for h in resp.points:
            p = h.payload or {}
            url = p.get("url", "")
            idx = p.get("chunk_index", 0)
            key = (url, idx)
            if key not in seen:
                seen.add(key)
                results.append({
                    "chunk_text": p.get("chunk_text", ""),
                    "url": url,
                    "metadata": p.get("metadata", {}),
                })
            if len(results) >= top_k:
                break
        if len(results) >= top_k:
            break
    return results[:top_k]


def truncate_contents_to_chunks(contents_obj: dict, max_chars_per_url: int = 4000) -> list[dict[str, Any]]:
    """
    Fallback when RAG disabled: truncate contents to chunk-like format.
    Returns list of {chunk_text, url, metadata} for curate prompt.
    """
    chunks: list[dict[str, Any]] = []
    inner = contents_obj.get("contents", contents_obj)
    if not isinstance(inner, dict):
        return chunks
    for url, data in inner.items():
        if not isinstance(data, dict):
            continue
        parts = []
        summary = (data.get("summary") or "").strip()
        if summary:
            parts.append(summary[:1500])
        for h in (data.get("highlights") or [])[:5]:
            t = (h if isinstance(h, str) else str(h))[:500].strip()
            if t:
                parts.append(t)
        text = (data.get("text") or "").strip()
        if text:
            remaining = max_chars_per_url - sum(len(p) for p in parts)
            if remaining > 0:
                parts.append(text[:remaining])
        combined = "\n".join(parts).strip()
        if combined:
            chunks.append({
                "chunk_text": combined,
                "url": url,
                "metadata": {"source": "truncated"},
            })
    return chunks


def delete_run(run_id: str) -> int:
    """Delete all points for run_id. Returns deleted count."""
    from qdrant_client.http import models as qdrant_models
    client = _get_client()
    result = client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=qdrant_models.FilterSelector(
            filter=qdrant_models.Filter(
                must=[qdrant_models.FieldCondition(key="run_id", match=qdrant_models.MatchValue(value=run_id))]
            )
        ),
    )
    return getattr(result, "status", 0) or 0
