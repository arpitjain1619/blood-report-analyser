import shutil
import os
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pipeline import analyze_report

app = FastAPI(title="Blood Report Analyser API")

# CORS: allows a browser-based frontend (like our future React app,
# running on a different port/origin) to actually call this API.
# Without this, browsers block the request by default for security reasons.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # wide open for local development; we'll restrict this later for production
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "Blood Report Analyser API is running"}


@app.post("/analyze-report")
async def analyze_report_endpoint(file: UploadFile = File(...)):
    # Basic validation: only accept image files
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image")

    # Save the uploaded file to a temporary location on disk,
    # since our existing analyze_report() function expects a file path,
    # not raw upload bytes.
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        result = analyze_report(tmp_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    finally:
        os.remove(tmp_path)  # always clean up the temp file, success or failure
