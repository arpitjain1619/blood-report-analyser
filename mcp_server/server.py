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

mcp = FastMCP("Blood Report Analyser")

@mcp.tool
def analyze_blood_report(image_url: str) -> dict:
    """
    Analyzes a blood test report image and returns categorized biomarker
    results (High/Low/Normal) along with personalized, non-diagnostic
    health guidance grounded in a curated medical knowledge base.

    Args:
        image_url: A URL pointing to the blood report image. If a relative
            path (starting with /uploads/), it will be resolved against
            this server's backend.

    Returns:
        A dictionary containing extracted biomarker values, categorized
        status, and general educational advice. This is not a medical
        diagnosis.
    """
    if image_url.startswith("/"):
        image_url = f"{BACKEND_BASE_URL}{image_url}"

    response = httpx.get(image_url, timeout=30)
    response.raise_for_status()
    image_bytes = response.content

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name

    try:
        return analyze_report(tmp_path)
    finally:
        os.remove(tmp_path)
