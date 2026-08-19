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

VISION_MODELS = [
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "google/gemma-4-26b-a4b-it:free",
]


def extract_biomarkers(image_path: str, max_retries_per_model: int = 2) -> dict:
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
                )
                raw_output = response.choices[0].message.content
                return json.loads(raw_output)

            except Exception as e:
                last_error = e
                wait_time = attempt * 5
                print(f"  Failed ({e}). Retrying in {wait_time}s...")
                time.sleep(wait_time)

        print(f"Giving up on {model}, moving to next fallback model...\n")

    # If we reach here, every model in the list failed
    raise last_error


if __name__ == "__main__":
    image_path = "sample_report.png"

    print(f"Extracting biomarkers from {image_path}...")
    biomarkers = extract_biomarkers(image_path)
    print("Extracted:", biomarkers)

    print("\nCategorizing...")
    categorized = categorize(biomarkers)

    print("\n--- RESULTS ---")
    for name, info in categorized.items():
        print(f"{name}: {info['value']} → {info['status']} (normal: {info.get('normal_range', 'N/A')})")

    print("\nGenerating personalized advice...")
    vector_store = load_vector_store()
    advice = generate_advice(categorized, vector_store)

    print("\n--- PERSONALIZED ADVICE ---")
    print(advice)
