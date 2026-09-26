import json
import os

_REPORT_DATA_PATH = os.path.join(os.path.dirname(__file__), "report_data.json")


def _normalize(text: str) -> str:
    """Lowercase and collapse whitespace/punctuation for tolerant matching."""
    if text is None:
        return ""
    cleaned = str(text).strip().lower()
    # collapse internal whitespace runs to a single space
    cleaned = " ".join(cleaned.split())
    # drop characters that labs vary on but don't change meaning
    for ch in ["-", "_", ".", "(", ")", ":", ","]:
        cleaned = cleaned.replace(ch, " ")
    cleaned = " ".join(cleaned.split())  # re-collapse after removals
    return cleaned


def _build_alias_index(report_data: dict) -> dict:
    """
    Build a reverse lookup: normalized-name -> canonical-name.
    Includes each canonical name (mapped to itself) and all its aliases.
    """
    index = {}
    for type_key, type_info in report_data.items():
        if type_key.startswith("_"):
            continue  # skip metadata like _note
        ranges = type_info.get("ranges", {})
        for canonical, spec in ranges.items():
            index[_normalize(canonical)] = canonical
            for alias in spec.get("aliases", []):
                index[_normalize(alias)] = canonical
    return index


def _load_report_data(path: str = _REPORT_DATA_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# Build the index once at import time (the data doesn't change at runtime).
_ALIAS_INDEX = _build_alias_index(_load_report_data())


def resolve_name(raw_name: str) -> str:
    """
    Resolve a raw extracted marker name to its canonical name.
    Falls back to the original name unchanged if no alias/canonical match
    is found (so unknown markers stay unknown — never mis-mapped).
    """
    canonical = _ALIAS_INDEX.get(_normalize(raw_name))
    return canonical if canonical is not None else raw_name


def resolve_biomarkers(biomarkers: dict) -> dict:
    """
    Return a copy of the biomarkers dict with every key resolved to its
    canonical name. Values (the nested {value, unit, printed_range} dicts,
    or plain values) are carried across unchanged.
    """
    resolved = {}
    for name, data in biomarkers.items():
        resolved[resolve_name(name)] = data
    return resolved
