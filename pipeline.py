import os
from dotenv import load_dotenv
from categorize import categorize
from retriever import load_vector_store
from advisor import generate_advice
from name_resolver import resolve_biomarkers
from detector import group_markers_by_type
from disclaimer import get_disclaimer
from extractor import extract_biomarkers, _extract_biomarkers_from_pdf

load_dotenv()

MOCK_AI = os.getenv("MOCK_AI", "false").lower() == "true"

# A report type needs at least this many markers to get its own full section
# in a mixed report. Types with fewer markers are pooled into an "isolated"
# section (shown, but flagged as low-confidence) rather than dressed up as a
# confident typed report.
SECTION_THRESHOLD = 2

NARRATIVE_NOT_SUPPORTED_MESSAGE = (
    "This looks like a text-based (narrative) report, which we can't analyze yet. "
    "Please consult a licensed doctor to interpret your report."
)

UNSUPPORTED_REPORT_MESSAGE = (
    "This doesn't appear to be a report type we currently support, so we can't "
    "provide an analysis. Please consult a licensed doctor to interpret your report."
)


def analyze_report(file_path: str, sex: str = None) -> dict:
    skipped_pages = []
    report_sex = None

    if file_path.lower().endswith(".pdf"):
        biomarkers, skipped_pages, report_sex = _extract_biomarkers_from_pdf(file_path)
    else:
        biomarkers, report_sex = extract_biomarkers(file_path)

    # Precedence: sex from the report wins; else caller-supplied; else None (general range).
    effective_sex = report_sex or sex

    biomarkers = resolve_biomarkers(biomarkers)

    # Group markers by their report type, then split into full sections
    # (types with enough markers) vs. isolated lone markers.
    groups = group_markers_by_type(biomarkers)
    groups.pop("unknown", None)  # markers in no known type are set aside

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
        sections.append(_build_section(markers, report_type, sex=effective_sex))

    # Pool any lone markers into a single "isolated" section.
    if isolated_markers:
        sections.append(_build_isolated_section(isolated_markers, sex=effective_sex))

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


def _build_section(markers: dict, report_type: str, sex: str = None) -> dict:
    """Categorize and advise one report type's markers into a full section."""
    findings = categorize(markers, report_type, sex=sex)

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


def _build_isolated_section(markers: dict, sex: str = None) -> dict:
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
        all_findings.extend(categorize(type_markers, report_type, sex=sex))

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