import sys
import os

# Add the project root (one level up from this file) to Python's import path,
# so we can import pipeline.py even though this file lives in a subfolder.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import base64
import tempfile
from fastmcp import FastMCP
from pipeline import analyze_report

mcp = FastMCP("Blood Report Analyser")


@mcp.tool
def analyze_blood_report(image_base64: str) -> dict:
    """
    Analyzes a blood test report image and returns categorized biomarker
    results (High/Low/Normal) along with personalized, non-diagnostic
    health guidance grounded in a curated medical knowledge base.

    Args:
        image_base64: The blood report image, encoded as a base64 string.

    Returns:
        A dictionary containing the extracted biomarker values, their
        categorized status against normal reference ranges, and general
        educational advice for any abnormal findings. This is not a
        medical diagnosis.
    """
    image_bytes = base64.b64decode(image_base64)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name

    try:
        return analyze_report(tmp_path)
    finally:
        os.remove(tmp_path)


if __name__ == "__main__":
    mcp.run()
