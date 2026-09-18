from reference_ranges import REFERENCE_RANGES

def categorize(biomarkers: dict) -> list:
    """
    Takes a dict of {biomarker_name: value} and returns a list of
    numeric finding-entries in the unified findings schema:
        {kind, name, value, unit, status, normal_range}
    """
    findings = []

    for name, value in biomarkers.items():
        if name not in REFERENCE_RANGES:
            findings.append({
                "kind": "numeric",
                "name": name,
                "value": value,
                "unit": "",
                "status": "Unknown (no reference range)",
                "normal_range": None,
            })
            continue

        ref = REFERENCE_RANGES[name]
        if value < ref["min"]:
            status = "Low"
        elif value > ref["max"]:
            status = "High"
        else:
            status = "Normal"

        findings.append({
            "kind": "numeric",
            "name": name,
            "value": value,
            "unit": ref["unit"],
            "status": status,
            "normal_range": f"{ref['min']}–{ref['max']} {ref['unit']}",
        })

    return findings
