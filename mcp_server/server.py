import sys
import os
import httpx

# Add the project root (one level up from this file) to Python's import path,
# so we can import pipeline.py even though this file lives in a subfolder.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tempfile
from fastmcp import FastMCP
from pipeline import analyze_report

BACKEND_BASE_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8001")

mcp = FastMCP("Health Report Analyser")
@mcp.tool
def analyze_blood_report(file_url: str) -> dict:
    """
    Analyzes a health lab report (image or PDF) and returns structured,
    non-diagnostic educational guidance grounded in a curated knowledge base.
    Supports several report types (e.g. blood/CBC, diabetes, lipid, thyroid,
    vitamins) and reports that mix multiple types in one document.

    Args:
        file_url: A URL pointing to the report file — an image (PNG/JPG) or a
            PDF. A relative path (starting with /uploads/) is resolved against
            this server's backend.

    Returns:
        A dictionary shaped as:
          {
            "sections": [
              {
                "report_type": "<e.g. blood, lipid, thyroid, or 'isolated'>",
                "findings": [
                  {"name", "value", "unit", "status",
                   "severity": "normal|attention|critical|unassessed",
                   "normal_range", "printed_range", "range_source"}
                ],
                "advice": {"summary": "...", "findings": [{"name", "advice"}]},
                "disclaimer": "..."
              }
            ],
            "skipped_pages": [<page numbers that could not be read, if any>]
          }
        A report may contain multiple sections (one per detected report type).
        Markers that appear in isolation are grouped under an "isolated"
        section and should be treated as low-confidence. This is educational
        information only and NOT a medical diagnosis.
    """
    if file_url.startswith("/"):
        file_url = f"{BACKEND_BASE_URL}{file_url}"

    response = httpx.get(file_url, timeout=30)
    response.raise_for_status()
    file_bytes = response.content

    # Preserve the file's extension so the pipeline can tell PDF from image.
    ext = os.path.splitext(file_url)[1].lower() or ".png"

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        return analyze_report(tmp_path)
    finally:
        os.remove(tmp_path)
