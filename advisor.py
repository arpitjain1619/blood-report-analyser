import os
import time
from dotenv import load_dotenv
from anthropic import Anthropic
from retriever import retrieve_relevant_chunks
from json_utils import extract_json

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


def generate_advice(findings: list, vector_store: list, report_type: str = None) -> dict:
    abnormal = [
        f for f in findings
        if f["kind"] == "numeric" and f.get("severity") == "attention"
    ]

    if not abnormal:
        return {
            "summary": "All biomarkers are within normal range. No specific concerns to flag.",
            "findings": [],
        }

    context_pieces = []
    for f in abnormal:
        query = f"{f['name']} is {f['status']}"
        matches = retrieve_relevant_chunks(query, vector_store, top_k=1, report_type=report_type)
        for match in matches:
            context_pieces.append(f"[Context for {f['name']} - {f['status']}]\n{match['text']}")

    retrieved_context = "\n\n".join(context_pieces)

    findings_summary = "\n".join(
        f"- {f['name']}: {f['value']} ({f['status']}, normal range: {f['normal_range']})"
        for f in abnormal
    )

    finding_names = [f["name"] for f in abnormal]

    prompt = f"""You are a health information assistant. A report shows the following abnormal findings:

{findings_summary}

Here is relevant reference information for these findings:

{retrieved_context}

Using ONLY the reference information above, write brief, general, educational guidance. Do not diagnose any condition. Do not recommend medications or dosages.

Respond with ONLY a JSON object in exactly this structure, no other text, no markdown code fences:
{{
  "summary": "a short overall note that may relate the findings to each other and always reminds the person to consult a licensed doctor to interpret the results",
  "findings": [
    {{"name": "<one of the finding names>", "advice": "general educational guidance for that finding"}}
  ]
}}

Include one findings entry for each of these findings: {finding_names}."""

    raw = call_model_with_fallback(prompt)

    # Try to parse structured output; degrade to summary-only if it fails.
    try:
        parsed = extract_json(raw)
        summary = parsed.get("summary", "")
        parsed_findings = parsed.get("findings", [])
        # keep only well-formed entries
        clean_findings = [
            {"name": item.get("name", ""), "advice": item.get("advice", "")}
            for item in parsed_findings
            if isinstance(item, dict) and item.get("advice")
        ]
        return {"summary": summary, "findings": clean_findings}
    except Exception:
        # Degrade: the model produced useful text but not valid structure.
        # Keep the advice by putting the raw text in summary.
        return {"summary": raw.strip(), "findings": []}
