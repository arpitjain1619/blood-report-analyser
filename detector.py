import json
import os

_REPORT_TYPES_PATH = os.path.join(os.path.dirname(__file__), "report_types.json")


def _load_report_types(path: str = _REPORT_TYPES_PATH) -> dict:
    """Load the report-type → signature-marker definitions from JSON."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def detect_report_type(biomarkers: dict, min_matches: int = 2) -> str:
    """
    Rule-based report-type detection.

    Looks at the extracted biomarker names and matches them against the
    signature markers for each known report type. Returns the best-matching
    report type, or "unknown" if nothing matches confidently.

    min_matches = how many signature markers must be present before we're
    willing to call it a match (guards against a single stray name).
    """
    report_types = _load_report_types()
    extracted_names = set(biomarkers.keys())

    best_type = "unknown"
    best_score = 0

    for type_key, type_info in report_types.items():
        signatures = set(type_info.get("signature_markers", []))
        matches = len(extracted_names & signatures)

        if matches >= min_matches and matches > best_score:
            best_score = matches
            best_type = type_key

    return best_type