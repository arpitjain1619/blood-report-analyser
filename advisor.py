import os
import time
from dotenv import load_dotenv
from anthropic import Anthropic
from retriever import retrieve_relevant_chunks

load_dotenv()

client = Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
)

TEXT_MODELS = [
    "claude-sonnet-4-5",
    "claude-haiku-4-5",
]

def call_model_with_fallback(prompt: str, max_retries_per_model: int = 2) -> str:
    last_error = None
    for model in TEXT_MODELS:
        for attempt in range(1, max_retries_per_model + 1):
            try:
                print(f"Trying model: {model} (attempt {attempt})...")
                response = client.messages.create(
                    model=model,
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.content[0].text
            except Exception as e:
                last_error = e
                wait_time = attempt * 5
                print(f"  Failed ({e}). Retrying in {wait_time}s...")
                time.sleep(wait_time)
        print(f"Giving up on {model}, moving to next fallback model...\n")
    raise last_error


def generate_advice(findings: list, vector_store: list) -> str:
    abnormal = [
        f for f in findings
        if f["kind"] == "numeric" and f["status"] in ("High", "Low")
    ]

    if not abnormal:
        return "All biomarkers are within normal range. No specific concerns to flag."

    context_pieces = []
    for f in abnormal:
        query = f"{f['name']} is {f['status']}"
        matches = retrieve_relevant_chunks(query, vector_store, top_k=1)
        for match in matches:
            context_pieces.append(f"[Context for {f['name']} - {f['status']}]\n{match['text']}")

    retrieved_context = "\n\n".join(context_pieces)

    findings_summary = "\n".join(
        f"- {f['name']}: {f['value']} ({f['status']}, normal range: {f['normal_range']})"
        for f in abnormal
    )

    prompt = f"""You are a health information assistant. A blood report shows the following abnormal findings:

{findings_summary}

Here is relevant reference information for these findings:

{retrieved_context}

Using ONLY the reference information above, write brief, general, educational guidance for the person about these findings. Do not diagnose any condition. Do not recommend medications or dosages. Always end by recommending they consult a licensed doctor to interpret the results."""

    return call_model_with_fallback(prompt)
