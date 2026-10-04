import json
import os

_REPORT_DATA_PATH = os.path.join("data", "report_data.json")


def _load_report_data(path: str = _REPORT_DATA_PATH) -> dict:
    """Load the unified report-type definitions (markers + ranges) from JSON."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def detect_report_type(biomarkers: dict, min_matches: int = 2) -> str:
    report_data = _load_report_data()
    extracted_names = set(biomarkers.keys())

    best_type = "unknown"
    best_score = 0

    for type_key, type_info in report_data.items():
        if type_key.startswith("_"):
            continue  # skip metadata keys like "_note"

        signatures = set(type_info.get("signature_markers", []))
        matches = len(extracted_names & signatures)

        if matches >= min_matches and matches > best_score:
            best_score = matches
            best_type = type_key

    return best_type


def group_markers_by_type(biomarkers: dict) -> dict:
    """Group markers by their report type (from report_data.json). Unknown -> 'unknown'."""
    report_data = _load_report_data()

    # Build a lookup: marker name -> the type it belongs to.
    marker_to_type = {}
    for type_key, type_info in report_data.items():
        if type_key.startswith("_"):
            continue
        for marker_name in type_info.get("ranges", {}):
            marker_to_type[marker_name] = type_key

    # Drop each extracted marker into its type's group.
    groups = {}
    for name, data in biomarkers.items():
        report_type = marker_to_type.get(name, "unknown")
        groups.setdefault(report_type, {})[name] = data

    return groups