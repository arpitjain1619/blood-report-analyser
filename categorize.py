import json
import os

_REPORT_DATA_PATH = os.path.join(os.path.dirname(__file__), "report_data.json")


def _load_report_data(path: str = _REPORT_DATA_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _categorize_range(name, value, spec):
    """Marker with a normal band: below min = Low, above max = High."""
    if value < spec["min"]:
        status = "Low"
        severity = "attention"
    elif value > spec["max"]:
        status = "High"
        severity = "attention"
    else:
        status = "Normal"
        severity = "normal"

    return {
        "kind": "numeric",
        "name": name,
        "value": value,
        "unit": spec.get("unit", ""),
        "status": status,
        "severity": severity,
        "normal_range": f"{spec['min']}–{spec['max']} {spec.get('unit', '')}".strip(),
    }


def _categorize_direction(name, value, spec):
    """
    One-sided marker. prefer='higher' -> only too-low is a concern;
    prefer='lower' -> only too-high is a concern.
    """
    prefer = spec.get("prefer")

    if prefer == "higher":
        threshold = spec["min"]
        if value < threshold:
            status, severity = "Low", "attention"
        else:
            status, severity = "Normal", "normal"
        normal_range = f"≥ {threshold} {spec.get('unit', '')}".strip()

    elif prefer == "lower":
        threshold = spec["max"]
        if value > threshold:
            status, severity = "High", "attention"
        else:
            status, severity = "Normal", "normal"
        normal_range = f"≤ {threshold} {spec.get('unit', '')}".strip()

    else:
        raise ValueError(f"'direction' marker {name} missing valid 'prefer' (got {prefer!r})")

    return {
        "kind": "numeric",
        "name": name,
        "value": value,
        "unit": spec.get("unit", ""),
        "status": status,
        "severity": severity,
        "normal_range": normal_range,
    }


def _categorize_bands(name, value, spec):
    """
    Marker evaluated against ordered named bands. Each band may have a 'min'
    and/or 'max'; the value falls into the band whose bounds it satisfies.
    The band supplies both the human label (status) and the severity.
    """
    bands = spec.get("bands", [])

    matched = None
    for band in bands:
        low = band.get("min")
        high = band.get("max")
        above_low = (low is None) or (value >= low)
        below_high = (high is None) or (value < high)
        if above_low and below_high:
            matched = band
            break

    if matched is None:
        # Value didn't fall into any defined band — treat as unassessable
        # rather than guess.
        return {
            "kind": "numeric",
            "name": name,
            "value": value,
            "unit": spec.get("unit", ""),
            "status": "Unknown (out of defined bands)",
            "severity": "unassessed",
            "normal_range": None,
        }

    # Build a human-readable "normal range" from the band(s) marked normal.
    normal_bands = [b for b in bands if b.get("severity") == "normal"]
    if normal_bands:
        lows = [b.get("min") for b in normal_bands if b.get("min") is not None]
        highs = [b.get("max") for b in normal_bands if b.get("max") is not None]
        
        unit = spec.get("unit", "")
        # If any normal band is open at the bottom (no min), normal has no lower
        # bound. If any is open at the top (no max), normal has no upper bound.
        open_bottom = any(b.get("min") is None for b in normal_bands)
        open_top = any(b.get("max") is None for b in normal_bands)
        lo = None if open_bottom else (min(lows) if lows else None)
        hi = None if open_top else (max(highs) if highs else None)

        if lo is not None and hi is not None:
            normal_range = f"{lo}–{hi} {unit}".strip()
        elif hi is not None:
            normal_range = f"< {hi} {unit}".strip()
        elif lo is not None:
            normal_range = f"≥ {lo} {unit}".strip()
        else:
            normal_range = None
    else:
        normal_range = None

    return {
        "kind": "numeric",
        "name": name,
        "value": value,
        "unit": spec.get("unit", ""),
        "status": matched["label"],
        "severity": matched.get("severity", "normal"),
        "normal_range": normal_range,
    }


def categorize(biomarkers: dict, report_type: str) -> list:
    """
    Takes {biomarker_name: value} plus the detected report_type, and returns a
    list of numeric finding-entries with a uniform shape:
        {kind, name, value, unit, status, severity, normal_range}
    Ranges are looked up from report_data.json for the given report_type.
    """
    report_data = _load_report_data()
    type_ranges = report_data.get(report_type, {}).get("ranges", {})

    findings = []

    for name, value in biomarkers.items():
        spec = type_ranges.get(name)

        if spec is None:
            # No reference range for this marker in this report type — we can't
            # assess it, so we say so honestly rather than guess.
            findings.append({
                "kind": "numeric",
                "name": name,
                "value": value,
                "unit": "",
                "status": "Unknown (no reference range)",
                "severity": "unassessed",
                "normal_range": None,
            })
            continue

        marker_kind = spec.get("kind", "range")

        if marker_kind == "range":
            findings.append(_categorize_range(name, value, spec))
        elif marker_kind == "direction":
            findings.append(_categorize_direction(name, value, spec))
        elif marker_kind == "bands":
            findings.append(_categorize_bands(name, value, spec))
        else:
            raise ValueError(f"Unknown marker kind '{marker_kind}' for {name}")

    return findings