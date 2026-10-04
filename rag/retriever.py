import json
import numpy as np
from rag.embedder import embed_text


def load_vector_store(path: str = "vector_store.json") -> list:
    with open(path, "r") as f:
        return json.load(f)


def cosine_similarity(vec_a: list, vec_b: list) -> float:
    a = np.array(vec_a)
    b = np.array(vec_b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def retrieve_relevant_chunks(query: str, vector_store: list, top_k: int = 2, report_type: str = None) -> list:
    """
    Embeds the query and returns the top_k most similar chunks.

    If report_type is given, only chunks tagged with that type are considered
    (hard filter) — so, e.g., a lipid query never retrieves a thyroid chunk.
    If no chunks match that type, returns an empty list, letting the caller
    fall back to generic guidance.
    """
    # Hard filter by report type before doing any scoring.
    if report_type is not None:
        candidates = [e for e in vector_store if e.get("type") == report_type]
    else:
        candidates = vector_store

    if not candidates:
        return []  # no matching-type chunks — caller handles the generic fallback

    query_vector = embed_text(query)

    scored_chunks = []
    for entry in candidates:
        score = cosine_similarity(query_vector, entry["embedding"])
        scored_chunks.append({
            "article": entry["article"],
            "type": entry.get("type"),
            "text": entry["text"],
            "score": score,
        })

    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    return scored_chunks[:top_k]
