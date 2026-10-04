# Health Report Analyzer

An **AI-powered medical report analysis pipeline**, built with Python and FastAPI.
Upload a photo or PDF of a lab report, and the system uses a **vision-language model
(VLM)** to extract biomarker values, a deterministic rules engine to categorize them
by report type, and **Retrieval-Augmented Generation (RAG)** to produce grounded,
structured, non-diagnostic health guidance.

It supports five report types — **blood (CBC), diabetes, lipid, thyroid, and
vitamins** — and handles a single upload that mixes several of them.

Built as a hands-on learning project to explore real-world **AI engineering** end to
end: multimodal LLM inference, structured output extraction, embeddings, semantic
search, type-filtered RAG, and production-minded concerns like multi-provider
abstraction, rate-limit resilience, multi-model fallback, guaranteed safety framing,
and mock-mode testing.

> ⚠️ **Educational project only.** Not a medical device, and not a substitute for
> professional medical advice. All generated guidance is general and non-diagnostic,
> and always recommends consulting a licensed doctor.

> **Medical content status:** the knowledge-base articles, reference ranges,
> sex-specific range variants, and critical-value thresholds are **AI-drafted and
> pending review by a qualified medical professional.** They are illustrative, not
> clinically authoritative. Do not rely on them for medical decisions.

> The React frontend lives in a separate repo and has not yet been reconnected to the
> current response shape. This README covers the Python/AI backend.

## Contents

- [What It Does](#what-it-does)
- [Supported Report Types](#supported-report-types)
- [Architecture](#architecture)
- [AI / ML Concepts Demonstrated](#ai--ml-concepts-demonstrated)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Running the API](#running-the-api)
- [Pipeline Walkthrough](#pipeline-walkthrough)
- [Reference Data Model](#reference-data-model)
- [Sex-Specific Ranges](#sex-specific-ranges)
- [Safety Framing](#safety-framing)
- [Narrative Reports (planned)](#narrative-reports-planned)
- [Resilience](#resilience)
- [Mock Mode](#mock-mode)
- [API Reference](#api-reference)
- [MCP Server](#mcp-server)
- [File-by-File Reference](#file-by-file-reference)
- [Extending the Knowledge Base](#extending-the-knowledge-base)
- [Roadmap](#roadmap)
- [Disclaimer](#disclaimer)

## What It Does

1. A client uploads an image or PDF of a lab report.
2. The FastAPI backend runs it through an AI pipeline:
   - A **VLM** (Anthropic Claude) reads the report and extracts each biomarker's name,
     value, on-report unit, and printed reference range as structured JSON — no OCR
     library, just a multimodal LLM call with a tightly constrained prompt. It also
     reads the patient's sex if the report states it. PDFs are rendered to page images
     first; a multi-page report is merged, and an unreadable page is skipped and
     reported rather than failing the whole report.
   - Extracted names are **normalized** to canonical names (e.g. `Hb` → `Hemoglobin`),
     markers are **grouped by report type**, and each value is **categorized** against
     that type's reference data — deterministic, non-AI, rule-based.
   - A report may contain **several types at once**. Each type with enough markers
     becomes its own **section**; lone markers are pooled into a low-confidence
     **"isolated"** section rather than dressed up as a confident report.
   - For every abnormal finding, the system performs **type-filtered semantic
     retrieval** (Gemini embeddings + cosine search over a local vector store),
     returning only chunks matching that report type.
   - Claude then **generates structured, per-finding** guidance per section, using
     *only* the retrieved context (grounding), never diagnosing.
3. The API returns a list of **sections** (each with report type, findings, structured
   advice, and a guaranteed disclaimer) plus any skipped pages, as JSON.

## Supported Report Types

| Type | Example markers | Notes |
|---|---|---|
| **blood** (CBC) | Hemoglobin, WBC, Platelets, RBC, MCV… | Range markers; several have critical thresholds; Hb/Hct/RBC have sex-specific ranges |
| **diabetes** | HbA1c, Fasting Blood Glucose | Named bands (Normal / Prediabetes / Diabetes / Very High) |
| **lipid** | Total Cholesterol, LDL, HDL, Triglycerides | Named tiers (Optimal … Very High); HDL inverted |
| **thyroid** | TSH, Free T4, Free T3, Total T4/T3 | Range markers; TSH has a critical threshold |
| **vitamins** | Vitamin D, Vitamin B12 | Vitamin D is one-sided (higher is better) |

A mixed upload returns one section per detected type. Lone markers go under an
`"isolated"` section. An unrecognized upload returns an honest `"unknown"` section.

## Architecture

One FastAPI process serves the HTTP API, static upload serving, and a mounted MCP
server. The whole pipeline is one function —
`core.pipeline.analyze_report(file_path, sex=None)` — called by the CLI, the FastAPI
endpoint, and the MCP tool.

```
Client (HTTP / CLI / MCP)
   │  image or PDF
   ▼
Stage 1 · Vision Extraction  (core/extractor, Claude)
   PDF→page images (skip bad pages) → {name:{value,unit,printed_range}} + sex
   ▼
Stage 2 · Normalize → Group by type   (name resolver, core/detector; deterministic)
   ▼
Stage 3 · Split into sections         (full sections vs. "isolated")
   ▼  (per section)
Stage 4 · Categorize + Type-Filtered Retrieval
   rule-based status + severity (sex-aware); Gemini embeddings; cosine search
   hard-filtered to the section's report type
   ▼  (per section)
Stage 5 · Grounded Structured Generation  (core/advisor, Claude)
   {summary, findings:[{name, advice}]}; guaranteed per-section disclaimer
   ▼
{sections:[...], skipped_pages:[...]}
```

Stages 1 and 5 call **Claude**; stage 4 embeds via **Gemini**; stages 2–3 and
categorization are plain Python. See `ARCHITECTURE.md` for the full breakdown.

## AI / ML Concepts Demonstrated

- **Multimodal LLM inference** — the VLM reads the report image directly (base64, in an
  Anthropic image content block), no separate OCR.
- **Structured output extraction** — strict JSON for extraction and advice, parsed with
  a fence-tolerant helper because models wrap JSON in code fences despite instructions.
- **Prompt engineering** — tightly scoped instructions with exact format examples.
- **Multi-provider abstraction** — Claude for generation/vision, Gemini for embeddings;
  a real lesson that provider APIs aren't interchangeable and not every provider offers
  every capability.
- **Embeddings & vector store** — a from-scratch JSON vector store queried via cosine
  similarity; no managed vector DB, to keep the mechanics transparent.
- **Chunking** — overlapping fixed-size word chunks.
- **Type-filtered RAG** — retrieved chunks are hard-filtered by report type, so a lipid
  finding never retrieves a thyroid article.
- **Multi-type sectioning** — one upload split into per-type sections, with lone markers
  surfaced honestly as low-confidence.
- **Grounding & hallucination mitigation** — the generation prompt restricts the model
  to only the retrieved context and forbids diagnosis/medication advice.
- **Structured, per-finding output** — advice as `{summary, findings:[{name, advice}]}`.
- **Guaranteed safety framing** — a doctor-consult disclaimer attached in code (not left
  to the model), present on every section.
- **Graded severity** — findings carry `normal` / `attention` / `critical` /
  `unassessed`; critical values escalate the disclaimer.
- **Sex-specific ranges** — report → caller → general precedence, never guessed.
- **Model fallback & resilience** — vision/text iterate a model list with retries.
- **Graceful partial failure** — an unreadable PDF page is skipped and reported.
- **Mock mode** — a `MOCK_AI` flag swaps in canned per-type data for free testing.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI, Uvicorn |
| Text + vision LLM | Anthropic Claude (`claude-sonnet-4-5`, `claude-haiku-4-5` fallback) |
| Embeddings | Google Gemini (`gemini-embedding-2-preview`, 3072-dim) |
| Vector store | Local JSON file (`vector_store.json`) — no external vector DB |
| Reference data | `data/report_data.json` |
| MCP server | FastMCP, mounted into the FastAPI app |
| Tunneling (dev) | ngrok |

> **Why two providers?** Anthropic has no embedding model, so embeddings use Gemini
> while generation/vision use Claude. Model IDs are volatile config.

## Project Structure

Library code is organized into packages; entry-point scripts stay at the root.

```
health-report-analyzer/
├── main.py                  # FastAPI app: /analyze-report, /upload; mounts MCP at /mcp
├── cli.py                   # command-line runner: python3 cli.py [file]
├── build_vector_store.py    # one-time: chunk + embed + type-tag articles -> vector_store.json
├── playground.py            # scratch file
├── core/
│   ├── pipeline.py           # analyze_report(): orchestration, grouping, sectioning
│   ├── extractor.py          # vision + PDF extraction (Claude)
│   ├── detector.py           # report-type detection + marker grouping
│   ├── categorize.py         # rule-based status + severity (range/direction/bands), sex-aware
│   └── advisor.py            # structured grounded advice (Claude) + model fallback
├── rag/
│   ├── load_articles.py      # reads articles/<type>/*.md, tagged by type
│   ├── chunker.py            # overlapping word chunks
│   ├── embedder.py           # text -> embedding (Gemini), with retry
│   └── retriever.py          # cosine search, hard-filtered by report type
├── data/
│   ├── report_data.json      # per-type markers, ranges, variants, aliases, disclaimers, critical thresholds
│   ├── disclaimer.py         # disclaimer lookup (default / per-type / critical)
│   └── mock_data.py          # per-type canned biomarkers + advice for MOCK_AI
├── utils/
│   ├── json_utils.py         # fence-tolerant JSON parsing (shared)
│   └── pdf_utils.py          # PDF pages -> images (PyMuPDF)
├── mcp_server/
│   └── server.py             # FastMCP tool: analyze_health_report(file_url)
├── articles/                 # RAG knowledge base — 21 articles in type subfolders
├── uploads/                  # uploaded files (gitignored)
├── vector_store.json         # generated embeddings (gitignored)
├── sample_report.png         # synthetic sample report
└── docs/                     # DECISIONS.md, SPRINT_BOARD.md
```

Each package has an `__init__.py`; imports are absolute-from-root (`core.`, `rag.`,
`data.`, `utils.`). **Run from the project root** — the reference-data path is
working-directory-relative.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate

pip install fastapi uvicorn anthropic google-genai python-dotenv numpy pillow fastmcp httpx pymupdf
```

> There is no `requirements.txt` yet, so dependencies are installed manually (the line
> above). Adding a requirements file is a tracked follow-up. Note: a virtualenv bakes in
> its absolute path, so if you rename/move the project folder you must recreate the venv.

Create a `.env` in the repo root:

```bash
ANTHROPIC_API_KEY=your-anthropic-key-here
GEMINI_API_KEY=your-gemini-key-here
MOCK_AI=false
MOCK_REPORT=blood
BACKEND_API_URL=http://127.0.0.1:8001
```

- `ANTHROPIC_API_KEY` — Claude (vision + text).
- `GEMINI_API_KEY` — Gemini (embeddings).
- `MOCK_AI` — `true` skips all real model calls and returns canned data.
- `MOCK_REPORT` — which mock type to return in mock mode (`blood`/`diabetes`/`lipid`/
  `thyroid`/`vitamins`); default `blood`; ignored in real mode.
- `BACKEND_API_URL` — base URL the MCP tool resolves relative `/uploads/...` paths against.

Build the vector store once (and after editing articles — real embedding calls):

```bash
python3 build_vector_store.py
```

## Running the API

```bash
uvicorn main:app --port 8001
```

> **Do not use `--reload` for real-mode runs** — it can restart mid-request during a long
> LLM call and discard in-progress work.

One process serves the REST API, static `/uploads/...`, and the MCP server at `/mcp`.

Run the pipeline directly from the command line:

```bash
MOCK_AI=true python3 cli.py           # analyze sample_report.png, no real AI calls
python3 cli.py path/to/report.pdf     # analyze any image or PDF (real mode)
```

This prints each section (report type, findings with status/severity/provenance,
structured advice, disclaimer) and any skipped pages.

## Pipeline Walkthrough

The entire pipeline is one function in `core/pipeline.py`, called by the FastAPI
endpoint, the MCP tool, and the CLI. Simplified:

```python
def analyze_report(file_path, sex=None):
    # Stage 1: vision extraction (PDF pages merged; bad pages skipped; sex read if present)
    if file_path.endswith(".pdf"):
        biomarkers, skipped_pages, report_sex = _extract_biomarkers_from_pdf(file_path)
    else:
        biomarkers, report_sex = extract_biomarkers(file_path); skipped_pages = []
    effective_sex = report_sex or sex          # report sex -> caller sex -> general

    biomarkers = resolve_biomarkers(biomarkers)        # normalize names

    # Stages 2-3: group markers by type; split into full sections vs. isolated lone markers
    groups = group_markers_by_type(biomarkers)
    sections = []
    for report_type, markers in groups.items():
        if len(markers) >= SECTION_THRESHOLD:
            sections.append(_build_section(markers, report_type, sex=effective_sex))
        else:
            ...pool into one isolated section...
    # (nothing recognized -> a single "unknown" section)

    return {"sections": sections, "skipped_pages": skipped_pages}
```

Each `_build_section` runs Stages 4–5 (categorize + type-filtered RAG advice) and
attaches a guaranteed per-section disclaimer.

## Reference Data Model

All per-type data lives in `data/report_data.json` (data, not code), keyed by report
type. Each type has a `display_name`, `category`, `signature_markers`, and `ranges`.
Each marker declares a `kind`:

```json
"Hemoglobin": { "kind": "range", "min": 13.0, "max": 17.0, "unit": "g/dL",
                "critical_low": 7.0, "critical_high": 20.0,
                "aliases": ["Hb", "HGB", "Haemoglobin"],
                "variants": { "male": {"min":13.5,"max":17.5},
                              "female": {"min":12.0,"max":15.5} } }

"HbA1c": { "kind": "bands", "unit": "%", "aliases": ["A1c", "HBA1C"],
           "bands": [ {"max":5.7,"label":"Normal","severity":"normal"},
                      {"min":5.7,"max":6.5,"label":"Prediabetes","severity":"attention"},
                      {"min":6.5,"label":"Diabetes","severity":"attention"} ] }
```

Top-level `_default_disclaimer` and `_critical_disclaimer` provide shared disclaimer
text (types may override). **All these values are illustrative and pending medical
review.**

## Sex-Specific Ranges

A few markers (Hemoglobin, Hematocrit, RBC) have sex-dependent normal ranges, carried in
a `variants` block (male/female); the general `min`/`max` is the default. The sex used is
chosen by precedence: the report's stated sex → a caller-supplied sex → otherwise the
general range (never guessed; only `"male"`/`"female"` accepted). A printed range on the
report still takes precedence over sex variants for range markers.

## Safety Framing

- **Guaranteed disclaimer** — every section carries a `disclaimer` attached in code, so
  it's present on every path (including the degrade-to-summary, isolated, and unknown
  cases).
- **Critical values** — a value past a `critical_low`/`critical_high` (range markers) or
  in a band marked `critical` gets `severity: "critical"` and escalates that section to a
  stronger disclaimer. Thresholds are defined only where reasonably established and
  calibrated conservatively; messaging stays calm and non-diagnostic.

## Narrative Reports (planned)

Narrative/text reports (radiology, pathology) are **not yet supported** — only numeric
reports are. A recorded decision (`docs/DECISIONS.md`, HRA-21) says narrative findings
will be **explained in plain language but not rated** (no status/severity) — significance
is left to a doctor. This decision is **pending confirmation in the medical review** and
gates the narrative work.

## Resilience

Both LLM call sites — vision (`core/extractor.py`) and text (`core/advisor.py`) — iterate
an ordered model list (`claude-sonnet-4-5` → `claude-haiku-4-5`) with retries/backoff.
The embedding call (`rag/embedder.py`) has its own retry loop (no fallback model — a known
gap). An unreadable PDF page is skipped and reported, not fatal.

## Mock Mode

Set `MOCK_AI=true` to bypass every real model call; `MOCK_REPORT` selects the type.
Extraction returns that type's canned biomarkers (sex `None` → general ranges) and advice
returns its canned structured advice (both from `data/mock_data.py`). Grouping,
categorization, sectioning, disclaimer, and assembly all run for real, so mock mode
exercises the full structure at zero cost — with the same output shape as real mode.

## API Reference

### `GET /`
Health check.

### `POST /analyze-report`
`multipart/form-data` with a single `file` field — an **image or a PDF**. Runs the
pipeline and returns the sections result.

```json
{
  "sections": [
    {
      "report_type": "blood",
      "findings": [
        { "kind": "numeric", "name": "Hemoglobin", "value": 10.6, "unit": "g/dL",
          "status": "Low", "severity": "attention",
          "normal_range": "13.0-17.0 g/dL", "printed_range": "13.0-17.0",
          "range_source": "report" }
      ],
      "advice": { "summary": "…", "findings": [ { "name": "Hemoglobin", "advice": "…" } ] },
      "disclaimer": "This analysis is educational only and is not a medical diagnosis…"
    }
  ],
  "skipped_pages": []
}
```

A mixed report returns multiple sections; lone markers appear under `"report_type":
"isolated"`; an unrecognized report returns a single `"unknown"` section. **Errors:** 400
(not an image/PDF), 500 (analysis failed after fallbacks). CORS is wide open (dev only).

### `POST /upload`
Saves an image/PDF to `uploads/` and returns `{ "url": "/uploads/<uuid>.<ext>" }`, so a
client can hand the MCP tool a fetchable URL.

## MCP Server

`mcp_server/server.py` exposes the pipeline as an MCP tool via FastMCP, mounted into the
FastAPI app (one process/port/tunnel):

```python
@mcp.tool
def analyze_health_report(file_url: str) -> dict:
    ...
```

The tool takes a `file_url` (image or PDF); a relative `/uploads/...` path is resolved
against `BACKEND_API_URL`, the file is fetched with httpx (extension preserved so PDFs
route correctly), run through `analyze_report()`, and the sections result returned.

For a remote client, expose it with ngrok (`ngrok http 8001`) and register
`https://<subdomain>/mcp`. (Free ngrok allows one tunnel at a time — a reason the MCP
server is mounted into the main app. MCP auth is currently None — dev only.)

## File-by-File Reference

| File | Role |
|---|---|
| `main.py` | FastAPI app, CORS, `/analyze-report` + `/upload`, mounts MCP at `/mcp` |
| `cli.py` | Command-line runner |
| `build_vector_store.py` | One-time: chunk + embed + type-tag → `vector_store.json` |
| `core/pipeline.py` | `analyze_report()` orchestration; grouping; sectioning |
| `core/extractor.py` | Vision + PDF extraction (Claude) |
| `core/detector.py` | Report-type detection; marker grouping |
| `core/categorize.py` | Rule-based status + severity (range/direction/bands), sex-aware |
| `core/advisor.py` | Structured grounded advice (Claude), with fallback |
| `rag/load_articles.py` | Loads articles from type subfolders, tagged by type |
| `rag/chunker.py` | Word-based overlapping chunker |
| `rag/embedder.py` | Text → embedding (Gemini), with retry |
| `rag/retriever.py` | Type-filtered cosine similarity search |
| `data/report_data.json` | Per-type markers, ranges, variants, aliases, disclaimers, critical thresholds |
| `data/disclaimer.py` | Disclaimer lookup |
| `data/mock_data.py` | Per-type canned biomarkers + advice for `MOCK_AI` |
| `utils/json_utils.py` | Fence-tolerant JSON parsing (shared) |
| `utils/pdf_utils.py` | PDF pages → images (PyMuPDF) |
| `mcp_server/server.py` | FastMCP tool `analyze_health_report` |
| `articles/` | RAG knowledge base — 21 articles in type subfolders |
| `sample_report.png` | Synthetic sample report |
| `playground.py` | Scratch file |

## Extending the Knowledge Base

To add coverage for a new condition within an existing report type:

1. Add a `.md` file to the relevant `articles/<type>/` subfolder (general, factual,
   non-diagnostic; keep the AI-drafted / pending-review discipline).
2. Add/adjust the marker (aliases, variants, critical thresholds) in
   `data/report_data.json`.
3. Re-run `python3 build_vector_store.py` (a full rebuild).

To add a new report type, add a top-level entry to `report_data.json` and a new
`articles/<type>/` subfolder, then rebuild.

## Roadmap

- [x] Vision-based extraction (multimodal LLM), images **and PDFs**
- [x] Five report types + report-type detection + name normalization
- [x] Rule-based categorization with graded severity + critical values
- [x] On-report unit/printed-range capture with precedence + provenance
- [x] Sex-specific reference ranges
- [x] Type-filtered RAG; structured per-finding advice with degrade-to-summary
- [x] Guaranteed disclaimers with critical escalation
- [x] Mixed-report support + isolated-marker handling; graceful PDF page skipping
- [x] Multi-provider (Claude + Gemini); retry + model fallback
- [x] FastAPI service + MCP tool
- [x] Module refactor (SRP) + package reorg (core/rag/data/utils) + blood→health rename
- [x] Narrative-handling design decision recorded (explain-not-rate; pending review)
- [ ] **Medical review** of articles, ranges, variants, and critical thresholds (key gate)
- [ ] Narrative/radiology report support — gated on the review
- [ ] Reconnect the frontend to the `sections` response shape
- [ ] Evaluation harness for retrieval/generation quality
- [ ] `requirements.txt` for reproducible setup
- [ ] MCP authentication; restrict CORS; real deployment
- [ ] Automated tests

## Disclaimer

This project generates general, educational health information only. It does not
diagnose conditions, recommend medications or dosages, and is not a substitute for
professional medical advice. Its medical content is AI-drafted and pending professional
review. Always consult a licensed doctor to interpret real lab results.
