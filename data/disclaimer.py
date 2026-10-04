import json
import os

_REPORT_DATA_PATH = os.path.join("data", "report_data.json")


def _load_report_data(path: str = _REPORT_DATA_PATH) -> dict:
    """Load the unified report-type definitions from JSON."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_disclaimer(report_type: str = None, has_critical: bool = False) -> str:
    """
    Return the disclaimer for a report. If has_critical is True, return the
    stronger critical disclaimer (a critical finding is present). Otherwise
    return the type's own disclaimer if it has one, else the shared default.
    """
    report_data = _load_report_data()
    default = report_data.get("_default_disclaimer", "")

    if has_critical:
        return report_data.get("_critical_disclaimer", default)

    if report_type and report_type in report_data:
        type_info = report_data[report_type]
        if isinstance(type_info, dict):
            return type_info.get("disclaimer", default)

    return default