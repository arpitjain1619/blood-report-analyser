import base64
import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic
from categorize import categorize
from detector import detect_report_type
from retriever import load_vector_store
from advisor import generate_advice

load_dotenv()

client = Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
)

MOCK_AI = os.getenv("MOCK_AI", "false").lower() == "true"

VISION_MODELS = [
    "claude-sonnet-4-5",
    "claude-haiku-4-5",
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
                response = client.messages.create(
                    model=model,
                    max_tokens=1024,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt_text},
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/png",
                                        "data": base64_image,
                                    },
                                },
                            ],
                        }
                    ],
                    timeout=30,
                )

                # Defensive check: don't assume the response is well-formed
                if not response.content or not response.content[0].text:
                    raise ValueError(f"Model {model} returned an empty/invalid response")

                raw_output = response.content[0].text
                return json.loads(raw_output)

            except Exception as e:
                last_error = e
                print(f"  Failed ({e}).")
        print(f"Giving up on {model}, moving to next fallback model...\n")
    raise last_error


def analyze_report(image_path: str) -> dict:
    biomarkers = extract_biomarkers(image_path)
    report_type = detect_report_type(biomarkers)
    findings = categorize(biomarkers)

    if MOCK_AI:
        from mock_data import MOCK_ADVICE
        print("[MOCK_AI] Skipping real advice generation, returning mock advice.")
        advice = MOCK_ADVICE
    else:
        vector_store = load_vector_store()
        advice = generate_advice(findings, vector_store)

    return {
        "report_type": report_type,
        "findings": findings,
        "advice": advice,
    }


if __name__ == "__main__":
    image_path = "sample_report.png"
    print(f"Analyzing {image_path}...")
    result = analyze_report(image_path)

    print(f"\n--- REPORT TYPE: {result['report_type']} ---")

    print("\n--- RESULTS ---")
    for f in result["findings"]:
        if f["kind"] == "numeric":
            normal = f["normal_range"] if f["normal_range"] is not None else "N/A"
            print(f"{f['name']}: {f['value']} → {f['status']} (normal: {normal})")
        elif f["kind"] == "narrative":
            print(f"[{f['section']}] {f['finding_text']}")

    print("\n--- PERSONALIZED ADVICE ---")
    print(result["advice"])