import json
import os

_REPORT_DATA_PATH = os.path.join(os.path.dirname(__file__), "report_data.json")


def _load_report_data(path: str = _REPORT_DATA_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)



def _categorize_printed_range(name, value, printed_bounds, printed_unit, printed_range_str):
    """
    Judge a value against a printed range (min, max), where either bound may be
    None (one-sided). Used only for 'range'-kind markers when the report printed
    a usable range.
    """
    low, high = printed_bounds

    if low is not None and value < low:
        status, severity = "Low", "attention"
    elif high is not None and value > high:
        status, severity = "High", "attention"
    else:
        status, severity = "Normal", "normal"

    return {
        "kind": "numeric",
        "name": name,
        "value": value,
        "unit": printed_unit,
        "status": status,
        "severity": severity,
        "normal_range": f"{printed_range_str} {printed_unit}".strip(),
        "printed_unit": printed_unit,
        "printed_range": printed_range_str,
        "range_source": "report",
    }


def _parse_printed_range(printed_range):
    """
    Parse a printed reference range into (min, max), where either bound may be
    None for a one-sided range. Handles:
      - two-sided:  "13.0-17.0", "13.0 – 17.0"
      - upper-only: "<200", "<=200", "≤ 200"   -> (None, 200)
      - lower-only: ">40",  ">=40",  "≥ 40"    -> (40, None)
    Returns None if it can't be parsed or is absent.
    """
    if not printed_range:  # handles None and ""
        return None

    text = str(printed_range).strip()
    # normalize dash and comparator variants
    text = text.replace("–", "-").replace("—", "-")
    text = text.replace("≤", "<=").replace("≥", ">=")

    try:
        # upper-only: "<200" or "<=200"
        if text.startswith("<="):
            return (None, float(text[2:].strip()))
        if text.startswith("<"):
            return (None, float(text[1:].strip()))
        # lower-only: ">40" or ">=40"
        if text.startswith(">="):
            return (float(text[2:].strip()), None)
        if text.startswith(">"):
            return (float(text[1:].strip()), None)

        # two-sided: "low-high"
        parts = text.split("-")
        if len(parts) == 2:
            low = float(parts[0].strip())
            high = float(parts[1].strip())
            return (low, high)
    except ValueError:
        return None

    return None


def _unpack_marker(raw):
    """
    Accept a marker's extracted data in the nested shape
    {value, unit, printed_range}. Returns (value, printed_unit, printed_range).
    """
    value = raw.get("value")
    printed_unit = raw.get("unit", "") or ""
    printed_range = raw.get("printed_range")
    return value, printed_unit, printed_range


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
    Takes {name: {value, unit, printed_range}} plus the detected report_type,
    and returns a list of numeric finding-entries with a uniform shape.

    Judgment precedence (HRA-07):
      - 'range' markers: use the report's printed range when it parses;
        otherwise fall back to the JSON reference range.
      - 'bands'/'direction' markers: always use the JSON model (a printed
        low-high can't express named tiers).
    Every finding also carries the printed unit/range for display, plus a
    'range_source' noting whether judgment used the report or the JSON data.
    """
    report_data = _load_report_data()
    type_ranges = report_data.get(report_type, {}).get("ranges", {})

    findings = []

    for name, raw in biomarkers.items():
        value, printed_unit, printed_range_str = _unpack_marker(raw)
        spec = type_ranges.get(name)

        if spec is None:
            findings.append({
                "kind": "numeric",
                "name": name,
                "value": value,
                "unit": printed_unit,
                "status": "Unknown (no reference range)",
                "severity": "unassessed",
                "normal_range": None,
                "printed_unit": printed_unit,
                "printed_range": printed_range_str,
                "range_source": "none",
            })
            continue

        marker_kind = spec.get("kind", "range")

        # For 'range' markers, prefer a usable printed range.
        if marker_kind == "range":
            printed_bounds = _parse_printed_range(printed_range_str)
            if printed_bounds is not None:
                findings.append(
                    _categorize_printed_range(
                        name, value, printed_bounds, printed_unit, printed_range_str
                    )
                )
                continue
            # else fall through to JSON range below

        # JSON-based judgment (all bands/direction, and range with no usable printed range)
        if marker_kind == "range":
            finding = _categorize_range(name, value, spec)
        elif marker_kind == "direction":
            finding = _categorize_direction(name, value, spec)
        elif marker_kind == "bands":
            finding = _categorize_bands(name, value, spec)
        else:
            raise ValueError(f"Unknown marker kind '{marker_kind}' for {name}")

        # Attach display fields + source. Prefer the printed unit for display;
        # fall back to the JSON unit the helper already set.
        finding["printed_unit"] = printed_unit
        finding["printed_range"] = printed_range_str
        finding["range_source"] = "data"
        if printed_unit:
            finding["unit"] = printed_unit

        findings.append(finding)

    return findings