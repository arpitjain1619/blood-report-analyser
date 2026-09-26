import base64
import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic
from categorize import categorize
from detector import detect_report_type
from retriever import load_vector_store
from advisor import generate_advice
from pdf_utils import pdf_to_images

load_dotenv()

client = Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
)

MOCK_AI = os.getenv("MOCK_AI", "false").lower() == "true"

VISION_MODELS = [
    "claude-sonnet-4-5",
    "claude-haiku-4-5",
]

UNSUPPORTED_REPORT_MESSAGE = (
    "This doesn't appear to be a report type we currently support, so we can't "
    "provide an analysis. Please consult a licensed doctor to interpret your report."
)


def extract_biomarkers(image_path: str, max_retries_per_model: int = 1) -> dict:
    if MOCK_AI:
        from mock_data import MOCK_BIOMARKERS
        print("[MOCK_AI] Skipping real vision call, returning mock biomarkers.")
        return MOCK_BIOMARKERS

    with open(image_path, "rb") as f:
        image_bytes = f.read()
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    prompt_text = """This is a medical lab report. Extract every biomarker/test and its details.

Respond with ONLY a JSON object, no other text, no markdown formatting, no code fences.
For each test, provide an object with:
  - "value": the numeric result (number only)
  - "unit": the unit exactly as printed on the report (e.g. "g/dL", "mg/dL"), or "" if none is shown
  - "printed_range": the reference/normal range exactly as printed on the report (e.g. "13.0-17.0"), or null if none is shown

Format exactly like this example:
{
  "Hemoglobin": {"value": 15.0, "unit": "g/dL", "printed_range": "13.0-17.0"},
  "Platelet Count": {"value": 265, "unit": "x10^3/uL", "printed_range": "150-450"}
}

Use the exact test names as they appear in the report."""

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


def _extract_biomarkers_from_pdf(pdf_path: str) -> dict:
    """
    Renders every page of a PDF to an image, runs vision extraction on each
    page, and merges all pages' biomarkers into one combined dict
    (Approach 1: a multi-page PDF is treated as ONE report split across pages).
    Temp page-images are always cleaned up.
    """
    page_images = pdf_to_images(pdf_path)
    merged = {}
    try:
        for img_path in page_images:
            page_biomarkers = extract_biomarkers(img_path)
            merged.update(page_biomarkers)
    finally:
        for img_path in page_images:
            if os.path.exists(img_path):
                os.remove(img_path)
    return merged


def analyze_report(file_path: str) -> dict:
    if file_path.lower().endswith(".pdf"):
        biomarkers = _extract_biomarkers_from_pdf(file_path)
    else:
        biomarkers = extract_biomarkers(file_path)

    report_type = detect_report_type(biomarkers)

    # If we can't confidently identify the report type, stop here — don't
    # categorize or generate advice for a report we don't understand.
    if report_type == "unknown":
        return {
            "report_type": "unknown",
            "findings": [],
            "advice": UNSUPPORTED_REPORT_MESSAGE,
        }

    findings = categorize(biomarkers, report_type)

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
            unit = f.get("unit", "")
            normal = f["normal_range"] if f["normal_range"] is not None else "N/A"
            source = f.get("range_source", "data")
            printed = f.get("printed_range")
            printed_note = f" [report printed: {printed}]" if printed else ""
            print(
                f"{f['name']}: {f['value']} {unit} → {f['status']} "
                f"({f['severity']}, normal: {normal}, via: {source}){printed_note}"
            )
        elif f["kind"] == "narrative":
            print(f"[{f['section']}] {f['finding_text']}")

    print("\n--- PERSONALIZED ADVICE ---")
    print(result["advice"])