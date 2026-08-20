import base64
import os
import json
import time
from dotenv import load_dotenv
from openai import OpenAI
from categorize import categorize
from retriever import load_vector_store
from advisor import generate_advice

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

MOCK_AI = os.getenv("MOCK_AI", "false").lower() == "true"

VISION_MODELS = [
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "google/gemma-4-26b-a4b-it:free",
]


def extract_biomarkers(image_path: str, max_retries_per_model: int = 1) -> dict:
    if MOCK_AI:
        from mock_data import MOCK_BIOMARKERS
        print("[MOCK_AI] Skipping real vision call, returning mock biomarkers.")
        return MOCK_BIOMARKERS

    with open(image_path, "rb") as f:
        image_bytes = f.read()
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    prompt_text = """This is a blood test report. Extract every biomarker name and its numeric value.

Respond with ONLY a JSON object, no other text, no markdown formatting, no code fences.
Format exactly like this example:
{"Hemoglobin": 15.0, "Platelet Count": 265}

Use the exact biomarker names as they appear in the report. Only include the value (number), not units."""

    last_error = None

    for model in VISION_MODELS:
        for attempt in range(1, max_retries_per_model + 1):
            try:
                print(f"Trying model: {model} (attempt {attempt})...")
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt_text},
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                            ]
                        }
                    ],
                    timeout=30,  # fail fast instead of hanging indefinitely
                )

                # Defensive check: don't assume the response is well-formed
                if not response.choices or not response.choices[0].message.content:
                    raise ValueError(f"Model {model} returned an empty/invalid response")

                raw_output = response.choices[0].message.content
                return json.loads(raw_output)

            except Exception as e:
                last_error = e
                print(f"  Failed ({e}).")
        print(f"Giving up on {model}, moving to next fallback model...\n")
    raise last_error


def analyze_report(image_path: str) -> dict:
    """
    The full pipeline as a reusable function:
    image path in -> {biomarkers, categorized, advice} out.
    This is what the FastAPI endpoint (and the CLI entry point below) both call.
    """
    biomarkers = extract_biomarkers(image_path)
    categorized = categorize(biomarkers)

    if MOCK_AI:
        from mock_data import MOCK_ADVICE
        print("[MOCK_AI] Skipping real advice generation, returning mock advice.")
        advice = MOCK_ADVICE
    else:
        vector_store = load_vector_store()
        advice = generate_advice(categorized, vector_store)

    return {
        "biomarkers": biomarkers,
        "categorized": categorized,
        "advice": advice,
    }


if __name__ == "__main__":
    image_path = "sample_report.png"
    print(f"Analyzing {image_path}...")
    result = analyze_report(image_path)

    print("\n--- RESULTS ---")
    for name, info in result["categorized"].items():
        print(f"{name}: {info['value']} → {info['status']} (normal: {info.get('normal_range', 'N/A')})")

    print("\n--- PERSONALIZED ADVICE ---")
    print(result["advice"])