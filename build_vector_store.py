import json
import time
from load_articles import load_articles
from chunker import chunk_text
from embedder import embed_text

def build_vector_store(output_path: str = "vector_store.json"):
    articles = load_articles()
    vector_store = []

    for filename, text in articles.items():
        chunks = chunk_text(text, chunk_size=60, overlap=15)
        for i, chunk in enumerate(chunks):
            print(f"Embedding {filename} — chunk {i+1}/{len(chunks)}...")
            vector = embed_text(chunk)
            vector_store.append({
                "article": filename,
                "chunk_index": i,
                "text": chunk,
                "embedding": vector,
            })
            time.sleep(1)  # small pause, kind to the free-tier rate limit

    with open(output_path, "w") as f:
        json.dump(vector_store, f)

    print(f"\nSaved {len(vector_store)} chunks (with embeddings) to {output_path}")


if __name__ == "__main__":
    build_vector_store()
