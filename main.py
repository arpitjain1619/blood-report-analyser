import shutil
import os
import tempfile
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pipeline import analyze_report
from mcp_server.server import mcp as mcp_server_instance

# Build the MCP sub-app first — its lifespan needs to be wired into
# the main FastAPI app at creation time, or session handling breaks.
mcp_app = mcp_server_instance.http_app(path="/")

app = FastAPI(title="Blood Report Analyser API", lifespan=mcp_app.lifespan)

# Mount the MCP server at /mcp — same external URL shape as before
# (http://host/mcp), just now living inside the same process/port
# as the rest of the backend, so one ngrok tunnel covers everything.
app.mount("/mcp", mcp_app)

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

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
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        result = analyze_report(tmp_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    finally:
        os.remove(tmp_path)


@app.post("/upload")
async def upload_report(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    os.makedirs("uploads", exist_ok=True)

    ext = os.path.splitext(file.filename)[1] or ".png"
    filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join("uploads", filename)

    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return {"url": f"/uploads/{filename}"}