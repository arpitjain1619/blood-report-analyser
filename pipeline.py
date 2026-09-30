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
from detector import detect_report_type, get_disclaimer, group_markers_by_type

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


def _extract_biomarkers_from_pdf(pdf_path: str) -> tuple:
    """
    Renders every page of a PDF to an image, runs vision extraction on each
    page, and merges all pages' biomarkers into one combined dict
    (a multi-page PDF is treated as ONE report split across pages).

    If a page can't be read (extraction fails after its retries), that page is
    skipped rather than failing the whole report. Returns:
        (merged_biomarkers, skipped_pages)
    where skipped_pages is a list of 1-based page numbers that failed.
    Temp page-images are always cleaned up.
    """
    page_images = pdf_to_images(pdf_path)
    merged = {}
    skipped_pages = []
    try:
        for index, img_path in enumerate(page_images):
            page_number = index + 1  # 1-based, friendlier for users
            try:
                page_biomarkers = extract_biomarkers(img_path)
                merged.update(page_biomarkers)
            except Exception as e:
                print(f"  Could not read page {page_number}, skipping it ({e}).")
                skipped_pages.append(page_number)
    finally:
        for img_path in page_images:
            if os.path.exists(img_path):
                os.remove(img_path)
    return merged, skipped_pages


def analyze_report(file_path: str) -> dict:
    skipped_pages = []

    if file_path.lower().endswith(".pdf"):
        biomarkers, skipped_pages = _extract_biomarkers_from_pdf(file_path)
    else:
        biomarkers = extract_biomarkers(file_path)

    biomarkers = resolve_biomarkers(biomarkers)

    # Group markers by their report type, then split into full sections
    # (types with enough markers) vs. isolated lone markers.
    groups = group_markers_by_type(biomarkers)
    groups.pop("unknown", None)  # markers in no known type are set aside

    SECTION_THRESHOLD = 2
    section_groups = {}      # types that earn a full section
    isolated_markers = {}    # lone markers, pooled together

    for report_type, markers in groups.items():
        if len(markers) >= SECTION_THRESHOLD:
            section_groups[report_type] = markers
        else:
            isolated_markers.update(markers)

    # Build a full section for each qualifying type.
    sections = []
    for report_type, markers in section_groups.items():
        sections.append(_build_section(markers, report_type))

    # Pool any lone markers into a single "isolated" section.
    if isolated_markers:
        sections.append(_build_isolated_section(isolated_markers))

    # No recognized markers at all -> honest unknown result.
    if not sections:
        sections.append({
            "report_type": "unknown",
            "findings": [],
            "advice": {"summary": UNSUPPORTED_REPORT_MESSAGE, "findings": []},
            "disclaimer": get_disclaimer(None),
        })

    return {
        "sections": sections,
        "skipped_pages": skipped_pages,
    }


def _build_section(markers: dict, report_type: str) -> dict:
    """Categorize and advise one report type's markers into a full section."""
    findings = categorize(markers, report_type)

    if MOCK_AI:
        from mock_data import get_mock_advice
        advice = get_mock_advice(report_type)
    else:
        vector_store = load_vector_store()
        advice = generate_advice(findings, vector_store, report_type)

    has_critical = any(f.get("severity") == "critical" for f in findings)

    return {
        "report_type": report_type,
        "findings": findings,
        "advice": advice,
        "disclaimer": get_disclaimer(report_type, has_critical=has_critical),
    }


def _build_isolated_section(markers: dict) -> dict:
    """
    Lone markers that didn't meet the section threshold. We still categorize them
    (grouped by their own type) so status/severity show, but present them as
    low-confidence isolated findings rather than a confident typed report — a
    single stray marker may be a misread.
    """
    all_findings = []

    # Categorize each lone marker against its own type so status/severity are real.
    groups = group_markers_by_type(markers)
    groups.pop("unknown", None)
    for report_type, type_markers in groups.items():
        all_findings.extend(categorize(type_markers, report_type))

    advice = {
        "summary": (
            "These markers appeared on their own, without enough related results "
            "to form a full report section. They may be incidental or misread, so "
            "treat them with caution. Please consult a licensed doctor to interpret "
            "them properly."
        ),
        "findings": [],
    }

    has_critical = any(f.get("severity") == "critical" for f in all_findings)

    return {
        "report_type": "isolated",
        "findings": all_findings,
        "advice": advice,
        "disclaimer": get_disclaimer(None, has_critical=has_critical),
    }


if __name__ == "__main__":
    import sys

    file_path = sys.argv[1] if len(sys.argv) > 1 else "sample_report.png"
    print(f"Analyzing {file_path}...")
    result = analyze_report(file_path)

    for section in result["sections"]:
        print(f"\n=== SECTION: {section['report_type']} ===")

        print("\n--- RESULTS ---")
        for f in section["findings"]:
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

        advice = section["advice"]
        print("\n--- ADVICE ---")
        if isinstance(advice, dict):
            print(advice.get("summary", ""))
            for item in advice.get("findings", []):
                print(f"\n• {item.get('name', '')}:")
                print(f"  {item.get('advice', '')}")
        else:
            print(advice)

        print("\n--- DISCLAIMER ---")
        print(section.get("disclaimer", ""))

    skipped = result.get("skipped_pages", [])
    if skipped:
        pages = ", ".join(str(p) for p in skipped)
        print(f"\n--- NOTE ---\nSome pages could not be read and were skipped: page {pages}.")