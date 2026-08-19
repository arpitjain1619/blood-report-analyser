import json
import numpy as np
from embedder import embed_text

def load_vector_store(path: str = "vector_store.json") -> list:
    with open(path, "r") as f:
        return json.load(f)

def cosine_similarity(vec_a: list, vec_b: list) -> float:
    a = np.array(vec_a)
    b = np.array(vec_b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def retrieve_relevant_chunks(query: str, vector_store: list, top_k: int = 2) -> list:
    """
    Embeds the query, compares it against every chunk in the vector store,
    and returns the top_k most similar chunks.
    """
    query_vector = embed_text(query)

    scored_chunks = []
    for entry in vector_store:
        score = cosine_similarity(query_vector, entry["embedding"])
        scored_chunks.append({
            "article": entry["article"],
            "text": entry["text"],
            "score": score,
        })

    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    return scored_chunks[:top_k]
