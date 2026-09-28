import base64
import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic
from categorize import categorize
from retriever import load_vector_store
from advisor import generate_advice
from pdf_utils import pdf_to_images
from name_resolver import resolve_biomarkers
from json_utils import extract_json
from detector import detect_report_type, get_disclaimer

load_dotenv()

client = Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
)

MOCK_AI = os.getenv("MOCK_AI", "false").lower() == "true"

VISION_MODELS = [
    "claude-sonnet-4-5",
    "claude-haiku-4-5",
]

NARRATIVE_NOT_SUPPORTED_MESSAGE = (
    "This looks like a text-based (narrative) report, which we can't analyze yet. "
    "Please consult a licensed doctor to interpret your report."
)

UNSUPPORTED_REPORT_MESSAGE = (
    "This doesn't appear to be a report type we currently support, so we can't "
    "provide an analysis. Please consult a licensed doctor to interpret your report."
)


def extract_biomarkers(image_path: str, max_retries_per_model: int = 1) -> dict:
    if MOCK_AI:
        from mock_data import get_mock_biomarkers
        mock_report = os.getenv("MOCK_REPORT", "blood")
        print(f"[MOCK_AI] Skipping real vision call, returning mock '{mock_report}' biomarkers.")
        return get_mock_biomarkers(mock_report)

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
                return extract_json(raw_output)

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


def _get_report_category(report_type: str) -> str:
    """Look up whether a report type is 'numeric' or 'narrative'."""
    import json
    path = os.path.join(os.path.dirname(__file__), "report_data.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get(report_type, {}).get("category", "numeric")


def _analyze_numeric(biomarkers: dict, report_type: str) -> dict:
    """The numeric pipeline: categorize values against ranges, then advise."""
    findings = categorize(biomarkers, report_type)

    if MOCK_AI:
        from mock_data import get_mock_advice
        mock_report = os.getenv("MOCK_REPORT", "blood")
        print("[MOCK_AI] Skipping real advice generation, returning mock advice.")
        advice = get_mock_advice(mock_report)
    else:
        vector_store = load_vector_store()
        advice = generate_advice(findings, vector_store, report_type)

    return {
        "report_type": report_type,
        "findings": findings,
        "advice": advice,
    }


def _analyze_narrative(biomarkers: dict, report_type: str) -> dict:
    """
    Placeholder for narrative (text-based) reports, e.g. radiology.
    Not built yet — see HRA-22/HRA-23. Returns an honest 'not supported' result.
    """
    return {
        "report_type": report_type,
        "findings": [],
        "advice": NARRATIVE_NOT_SUPPORTED_MESSAGE,
    }


def analyze_report(file_path: str) -> dict:
    if file_path.lower().endswith(".pdf"):
        biomarkers = _extract_biomarkers_from_pdf(file_path)
    else:
        biomarkers = extract_biomarkers(file_path)

    biomarkers = resolve_biomarkers(biomarkers)

    report_type = detect_report_type(biomarkers)

    if report_type == "unknown":
        result = {
            "report_type": "unknown",
            "findings": [],
            "advice": UNSUPPORTED_REPORT_MESSAGE,
        }
    else:
        category = _get_report_category(report_type)
        if category == "narrative":
            result = _analyze_narrative(biomarkers, report_type)
        else:
            result = _analyze_numeric(biomarkers, report_type)

    # Guarantee a disclaimer on every result, regardless of type or model output.
    has_critical = any(
        f.get("severity") == "critical"
        for f in result.get("findings", [])
    )
    result["disclaimer"] = get_disclaimer(result.get("report_type"), has_critical=has_critical)
    return result


if __name__ == "__main__":
    import sys

    file_path = sys.argv[1] if len(sys.argv) > 1 else "sample_report.png"
    print(f"Analyzing {file_path}...")
    result = analyze_report(file_path)

    print(f"\n--- REPORT TYPE: {result['report_type']} ---")

    print("\n--- RESULTS ---")
    for f in result["findings"]:
        if f["kind"] == "numeric":
            unit = f.get("unit", "")
            normal = f["normal_range"] if f["normal_range"] is not None else "N/A"
            source = f.get("range_source", "data")
            printed = f.get("printed_range")
            printed_note = f" [report printed: {printed}]" if printed else ""
            flag = "  ⚠ CRITICAL" if f.get("severity") == "critical" else ""
            print(
                f"{f['name']}: {f['value']} {unit} → {f['status']} "
                f"({f['severity']}, normal: {normal}, via: {source}){printed_note}{flag}"
            )
        elif f["kind"] == "narrative":
            print(f"[{f['section']}] {f['finding_text']}")

    print("\n--- PERSONALIZED ADVICE ---")
    advice = result["advice"]
    if isinstance(advice, dict):
        print(advice.get("summary", ""))
        for item in advice.get("findings", []):
            print(f"\n• {item.get('name', '')}:")
            print(f"  {item.get('advice', '')}")
    else:
        # Backward-safe: if advice is ever a plain string, print it directly.
        print(advice)
    print("\n--- DISCLAIMER ---")
    print(result.get("disclaimer", ""))