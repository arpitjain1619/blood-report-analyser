from reference_ranges import REFERENCE_RANGES

def categorize(biomarkers: dict) -> dict:
    """
    Takes a dict of {biomarker_name: value} and returns a dict of
    {biomarker_name: {"value": ..., "status": ..., "range": ...}}
    """
    results = {}

    for name, value in biomarkers.items():
        if name not in REFERENCE_RANGES:
            # We don't have a reference range for this one — flag it, don't guess
            results[name] = {"value": value, "status": "Unknown (no reference range)"}
            continue

        ref = REFERENCE_RANGES[name]
        if value < ref["min"]:
            status = "Low"
        elif value > ref["max"]:
            status = "High"
        else:
            status = "Normal"

        results[name] = {
            "value": value,
            "status": status,
            "normal_range": f"{ref['min']}–{ref['max']} {ref['unit']}"
        }

    return results
