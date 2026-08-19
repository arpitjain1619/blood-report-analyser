from retriever import load_vector_store, retrieve_relevant_chunks

vector_store = load_vector_store()

query = "Hemoglobin is Low"
results = retrieve_relevant_chunks(query, vector_store, top_k=2)

print(f"Query: {query}\n")
for i, r in enumerate(results):
    print(f"--- Match {i+1} (score: {r['score']:.4f}, from {r['article']}) ---")
    print(r["text"])
    print()

