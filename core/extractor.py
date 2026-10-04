import base64
import os
from dotenv import load_dotenv
from anthropic import Anthropic
from utils.pdf_utils import pdf_to_images
from utils.json_utils import extract_json

load_dotenv()

client = Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
)

MOCK_AI = os.getenv("MOCK_AI", "false").lower() == "true"

VISION_MODELS = [
    "claude-sonnet-4-5",
    "claude-haiku-4-5",
]


def extract_biomarkers(image_path: str, max_retries_per_model: int = 1) -> tuple:
    if MOCK_AI:
        from data.mock_data import get_mock_biomarkers
        mock_report = os.getenv("MOCK_REPORT", "blood")
        print(f"[MOCK_AI] Skipping real vision call, returning mock '{mock_report}' biomarkers.")
        return get_mock_biomarkers(mock_report), None

    with open(image_path, "rb") as f:
        image_bytes = f.read()
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    prompt_text = """This is a medical lab report. Extract the patient's sex and every biomarker/test with its details.

Respond with ONLY a JSON object, no other text, no markdown, no code fences, in exactly this shape:
{
  "sex": "male" | "female" | null,
  "biomarkers": {
    "Hemoglobin": {"value": 15.0, "unit": "g/dL", "printed_range": "13.0-17.0"}
  }
}

For "sex": use the patient's sex if clearly shown on the report, otherwise null. Do not guess.
For each biomarker provide "value" (number), "unit" (as printed, or ""), and "printed_range" (as printed, or null).
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

                if not response.content or not response.content[0].text:
                    raise ValueError(f"Model {model} returned an empty/invalid response")

                raw_output = response.content[0].text
                parsed = extract_json(raw_output)

                sex = parsed.get("sex")
                biomarkers = parsed.get("biomarkers", {})

                # Only accept clean, expected sex values; anything else -> None,
                # so a misread never picks a wrong variant range.
                if sex not in ("male", "female"):
                    sex = None

                return biomarkers, sex

            except Exception as e:
                last_error = e
                print(f"  Failed ({e}).")
        print(f"Giving up on {model}, moving to next fallback model...\n")

    raise last_error


def _extract_biomarkers_from_pdf(pdf_path: str) -> tuple:
    """
    Renders every page of a PDF to an image, extracts each, and merges all
    pages' biomarkers into one combined dict. Takes the first sex found across
    pages. A page that fails extraction is skipped (not fatal) and its 1-based
    number recorded. Returns (merged_biomarkers, skipped_pages, sex).
    Temp page-images are always cleaned up.
    """
    page_images = pdf_to_images(pdf_path)
    merged = {}
    skipped_pages = []
    sex = None

    try:
        for index, img_path in enumerate(page_images):
            page_number = index + 1
            try:
                page_biomarkers, page_sex = extract_biomarkers(img_path)
                merged.update(page_biomarkers)
                if sex is None and page_sex is not None:
                    sex = page_sex  # first page that reports a sex wins
            except Exception as e:
                print(f"  Could not read page {page_number}, skipping it ({e}).")
                skipped_pages.append(page_number)
    finally:
        for img_path in page_images:
            if os.path.exists(img_path):
                os.remove(img_path)

    return merged, skipped_pages, sex