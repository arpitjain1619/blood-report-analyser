import os
import time
from dotenv import load_dotenv
from openai import OpenAI
from retriever import retrieve_relevant_chunks

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

TEXT_MODELS = [
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "google/gemma-4-26b-a4b-it:free",
]

def call_model_with_fallback(prompt: str, max_retries_per_model: int = 2) -> str:
    last_error = None
    for model in TEXT_MODELS:
        for attempt in range(1, max_retries_per_model + 1):
            try:
                print(f"Trying model: {model} (attempt {attempt})...")
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.choices[0].message.content
            except Exception as e:
                last_error = e
                wait_time = attempt * 5
                print(f"  Failed ({e}). Retrying in {wait_time}s...")
                time.sleep(wait_time)
        print(f"Giving up on {model}, moving to next fallback model...\n")
    raise last_error


def generate_advice(categorized: dict, vector_store: list) -> str:
    abnormal = {
        name: info for name, info in categorized.items()
        if info["status"] in ("High", "Low")
    }

    if not abnormal:
        return "All biomarkers are within normal range. No specific concerns to flag."

    context_pieces = []
    for name, info in abnormal.items():
        query = f"{name} is {info['status']}"
        matches = retrieve_relevant_chunks(query, vector_store, top_k=1)
        for match in matches:
            context_pieces.append(f"[Context for {name} - {info['status']}]\n{match['text']}")

    retrieved_context = "\n\n".join(context_pieces)

    findings_summary = "\n".join(
        f"- {name}: {info['value']} ({info['status']}, normal range: {info['normal_range']})"
        for name, info in abnormal.items()
    )

    prompt = f"""You are a health information assistant. A blood report shows the following abnormal findings:

{findings_summary}

Here is relevant reference information for these findings:

{retrieved_context}

Using ONLY the reference information above, write brief, general, educational guidance for the person about these findings. Do not diagnose any condition. Do not recommend medications or dosages. Always end by recommending they consult a licensed doctor to interpret the results."""

    return call_model_with_fallback(prompt)
