# Health Report Analyzer

An **AI-powered medical report analysis pipeline**, built with Python and
FastAPI. Upload a photo or PDF of a lab report, and the system uses a
**vision-language model (VLM)** to extract biomarker values, a deterministic
rules engine to categorize them by report type, and **Retrieval-Augmented
Generation (RAG)** to produce grounded, structured, non-diagnostic health
guidance.

Originally a blood-report-only tool, it has since been generalized into a
multi-report-type **Health Report Analyzer** that currently supports five
report types: **blood (CBC), diabetes, lipid, thyroid, and vitamins** — and
handles a single upload that mixes several of them.

Built as a hands-on learning project to explore real-world **AI engineering**
end to end: multimodal LLM inference, structured output extraction, embeddings,
semantic search, type-filtered RAG, and production-minded concerns like
multi-provider abstraction, rate-limit resilience, multi-model fallback,
guaranteed safety framing, and mock-mode testing.

> ⚠️ **Educational project only.** Not a medical device, and not a substitute
> for professional medical advice. All generated guidance is general and
> non-diagnostic, and always recommends consulting a licensed doctor.

> **Medical content status:** the knowledge-base articles, reference ranges,
> sex-specific range variants, and critical-value thresholds are currently
> **AI-drafted and pending review by a qualified medical professional.** They
> are illustrative, not clinically authoritative. Do not rely on them for
> medical decisions.

> This repo used to also contain a React frontend; it has since been split out
> into its own separate project. This README covers the Python/AI backend
> exclusively. (The frontend has not yet been updated to the current backend
> response shape.)

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
- [Stage 1 — Vision Extraction](#stage-1--vision-extraction)
- [Stage 2 — Detection, Normalization & Categorization](#stage-2--detection-normalization--categorization)
- [Stage 3 — Grouping into Sections](#stage-3--grouping-into-sections)
- [Stage 4 & 5 — Type-Filtered RAG](#stage-4--5--type-filtered-rag)
- [Reference Data Model](#reference-data-model)
- [Sex-Specific Ranges](#sex-specific-ranges)
- [Safety Framing: Disclaimers & Critical Values](#safety-framing-disclaimers--critical-values)
- [Narrative Reports (planned)](#narrative-reports-planned)
- [Resilience: Retries & Multi-Model Fallback](#resilience-retries--multi-model-fallback)
- [Mock Mode](#mock-mode)
- [API Reference](#api-reference)
- [MCP Server & ChatGPT Integration](#mcp-server--chatgpt-integration)
- [File-by-File Reference](#file-by-file-reference)
- [Extending the Knowledge Base](#extending-the-knowledge-base)
- [Roadmap](#roadmap)
- [Disclaimer](#disclaimer)

## What It Does

1. A client uploads an image or PDF of a lab report to the API.
2. The FastAPI backend runs it through an AI pipeline:
   - A **vision-language model (VLM)** reads the report and extracts each
     biomarker's name, value, on-report unit, and printed reference range as
     structured JSON — no OCR library, just a multimodal LLM call with a
     tightly constrained prompt. It also reads the patient's sex when the report
     states it. PDFs are rendered to page images first; a multi-page report is
     merged into one, and an unreadable page is skipped (and reported) rather
     than failing the whole report.
   - Extracted names are **normalized** to canonical names (e.g. `Hb` →
     `Hemoglobin`), markers are **grouped by report type**, and each value is
     **categorized** against that type's reference data — a deterministic,
     non-AI step, deliberately kept rule-based.
   - A report may contain **several types at once** (a checkup packet with blood
     + lipid + thyroid). Each type with enough markers becomes its own
     **section**; lone markers are pooled into a low-confidence **"isolated"**
     section rather than dressed up as a confident report.
   - For every abnormal finding, the system performs **type-filtered semantic
     retrieval**: it embeds a query, searches a **vector store** of
     report-type-tagged guidance articles by **cosine similarity**, and pulls
     back only chunks matching that report type (**RAG retrieval**).
   - An LLM then **generates structured, per-finding** guidance per section,
     explicitly instructed to use *only* the retrieved context — a **grounding**
     strategy that reduces hallucination risk.
3. The API returns a list of **sections** (each with its report type, findings,
   structured advice, and a guaranteed disclaimer) plus any skipped pages, as
   JSON.

## Supported Report Types

| Type | Example markers | Notes |
|---|---|---|
| **blood** (CBC) | Hemoglobin, WBC, Platelets, RBC, MCV… | Range markers; several have critical thresholds; Hb/Hct/RBC have sex-specific ranges |
| **diabetes** | HbA1c, Fasting Blood Glucose | Named bands (Normal / Prediabetes / Diabetes / Very High) |
| **lipid** | Total Cholesterol, LDL, HDL, Triglycerides | Named tiers (Optimal … Very High); HDL inverted |
| **thyroid** | TSH, Free T4, Free T3, Total T4/T3 | Range markers; TSH has a critical threshold |
| **vitamins** | Vitamin D, Vitamin B12 | Vitamin D is one-sided (higher is better) |

An upload with no recognized markers returns an honest "not supported" result
rather than a guess. An upload mixing several types returns one section per type.

## Architecture

One request, traced top to bottom — report in at the top, sections back out at
the bottom:

```
┌──────────────────────────────────────────────────┐
│                    API Client                     │
│      (any HTTP client, or an MCP client)          │
└──────────────────────────────────────────────────┘
                          │  1. upload report (image or PDF)
                          │     POST /analyze-report (multipart/form-data)
                          ▼
┌──────────────────────────────────────────────────┐
│                 FastAPI Backend (main.py)         │
└──────────────────────────────────────────────────┘
                          │  2. pipeline.analyze_report(file)
                          ▼
┌──────────────────────────────────────────────────┐
│      Stage 1 · Vision Extraction                  │
│  PDF→page images (skip bad pages) → VLM reads     │
│  → {name:{value,unit,printed_range}} + sex        │
│  Anthropic Claude vision + model fallback         │
└──────────────────────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────┐
│   Stage 2 · Normalize → Group by type             │
│  name resolution → look up each marker's type →   │
│  group markers per type (report_data.json)        │
│  (deterministic; no model call)                   │
└──────────────────────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────┐
│   Stage 3 · Split into sections                   │
│  type with >= threshold markers -> full section;  │
│  lone markers -> one "isolated" section           │
└──────────────────────────────────────────────────┘
                          ▼  (per section)
┌──────────────────────────────────────────────────┐
│   Stage 4 · Categorize + Type-Filtered Retrieval  │
│  rule-based status + severity (sex-aware);        │
│  embed query → cosine search over vector_store    │
│  hard-filtered to the section's report type       │
│  (embeddings: Google Gemini)                      │
└──────────────────────────────────────────────────┘
                          ▼  (per section)
┌──────────────────────────────────────────────────┐
│   Stage 5 · Grounded Structured Generation        │
│  LLM writes {summary, findings:[{name, advice}]}  │
│  from retrieved chunks; Claude + fallback;        │
│  guaranteed per-section disclaimer                 │
└──────────────────────────────────────────────────┘
                          │  3. {sections:[...], skipped_pages:[...]}
                          ▼
┌──────────────────────────────────────────────────┐
│                 FastAPI Backend → JSON response   │
└──────────────────────────────────────────────────┘
```

Stages 1 and 5 call **Anthropic Claude**; stage 4 embeds via **Google Gemini**
and does a local cosine search; stages 2–3 and the categorization in stage 4 are
plain deterministic Python, no model call. (Two providers because Anthropic has
no embedding model — see [Tech Stack](#tech-stack).)

## AI / ML Concepts Demonstrated

- **Multimodal LLM inference** — a vision-language model reads the report image
  directly (base64, in an Anthropic image content block) rather than via a
  separate OCR pipeline.
- **Structured output extraction** — the model returns strict JSON for both
  extraction and advice; parsed defensively with a fence-tolerant helper
  (`json_utils.extract_json`) because real models often wrap JSON in code
  fences despite instructions.
- **Prompt engineering** — tightly scoped instructions with exact format
  examples for reliable, parseable output.
- **Multi-provider abstraction** — generation/vision on Anthropic, embeddings
  on Google Gemini; a real lesson that provider APIs are *not* interchangeable
  and that not every provider offers every capability.
- **Embeddings & vector store** — a lightweight from-scratch vector store (a
  JSON file of `{text, embedding, type}` records) queried via manual **cosine
  similarity**, deliberately avoiding a managed vector DB to keep retrieval
  mechanics transparent.
- **Chunking** — articles split into overlapping fixed-size word chunks.
- **Type-filtered RAG** — retrieved chunks are **hard-filtered by report type**
  before scoring, so a lipid finding can never retrieve a thyroid article.
- **Multi-type sectioning** — one upload is split into per-type sections, with
  lone markers surfaced honestly as low-confidence rather than fabricated into a
  confident report.
- **Grounding & hallucination mitigation** — the generation prompt restricts
  the model to *only* the retrieved context and forbids diagnosis or medication
  advice.
- **Structured, per-finding output** — advice is returned as
  `{summary, findings:[{name, advice}]}`, not one blob.
- **Guaranteed safety framing** — a doctor-consult disclaimer is attached in
  code (not left to the model), so it's present on every section, including
  fallback and isolated/unknown cases.
- **Graded severity** — findings carry `normal` / `attention` / `critical` /
  `unassessed`, with critical values escalating the disclaimer calmly.
- **Sex-specific ranges** — where clinically established (Hb, Hct, RBC), the
  normal range is chosen by the patient's sex (from the report, else caller
  input, else the general range).
- **Model fallback & resilience** — vision and text steps iterate a list of
  models with retries/backoff.
- **Graceful partial failure** — an unreadable PDF page is skipped and
  reported, not fatal.
- **Mock mode** — a `MOCK_AI` flag swaps in canned per-type data for testing
  without spending quota.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI, Uvicorn |
| Text + vision LLM | [Anthropic Claude](https://www.anthropic.com) (`claude-sonnet-4-5`, with `claude-haiku-4-5` fallback) |
| Embeddings | [Google Gemini](https://ai.google.dev) (`gemini-embedding-2-preview`, 3072-dim) |
| Vector store | Local JSON file (`vector_store.json`) — no external vector DB |
| Reference data | `report_data.json` — per-type markers, ranges, aliases, variants, disclaimers, critical thresholds |
| MCP server | [FastMCP](https://github.com/jlowin/fastmcp), mounted into the FastAPI app |
| Tunneling (dev) | [ngrok](https://ngrok.com) — public HTTPS URL for remote MCP clients |

> **Why two providers?** Anthropic does not offer an embedding model, so
> embeddings use Google Gemini while generation/vision use Claude. Model IDs
> are volatile config, not fixed architecture.

## Project Structure

```
health-report-analyzer/
├── main.py                 # FastAPI app: /analyze-report, /upload, mounts MCP at /mcp
├── mcp_server/
│   └── server.py            # FastMCP server: analyze tool
├── pipeline.py              # Orchestrates the pipeline (file → sections); PDF handling; grouping
├── detector.py              # Report-type detection, marker grouping, disclaimer accessor
├── name_resolver.py         # Normalizes lab-specific marker names → canonical
├── categorize.py            # Rule-based status + severity (range / direction / bands), sex-aware
├── report_data.json         # Per-type data: markers, ranges, variants, aliases, disclaimers, critical thresholds
├── load_articles.py         # Loads knowledge-base articles from type subfolders, tagged by type
├── chunker.py               # Splits article text into overlapping chunks
├── embedder.py              # Text → embedding vector (Google Gemini), with retry
├── build_vector_store.py    # One-time script: chunk + embed all articles → vector_store.json (type-tagged)
├── retriever.py             # Cosine similarity search, hard-filtered by report type
├── advisor.py               # RAG prompt + structured grounded advice (Anthropic), with fallback
├── json_utils.py            # Fence-tolerant JSON parsing shared by extraction and advice
├── mock_data.py             # Per-type canned biomarkers + advice for MOCK_AI mode
├── pdf_utils.py             # Renders PDF pages to images (PyMuPDF)
├── articles/                # RAG knowledge base — 21 articles in type subfolders (blood/, lipid/, …)
├── uploads/                 # Images uploaded via /upload (gitignored)
├── vector_store.json        # Generated embeddings (gitignored)
├── sample_report.png        # Synthetic sample report for testing
└── playground.py            # Scratch file
```

## Setup

```bash
python3 -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate

pip install fastapi uvicorn anthropic google-genai python-dotenv numpy pillow fastmcp httpx pymupdf
```

Create a `.env` file in the repo root:

```bash
ANTHROPIC_API_KEY=your-anthropic-key-here
GEMINI_API_KEY=your-gemini-key-here
MOCK_AI=false
MOCK_REPORT=blood
BACKEND_API_URL=http://127.0.0.1:8001
```

- `ANTHROPIC_API_KEY` — for Claude (vision + text generation).
- `GEMINI_API_KEY` — for Google Gemini (embeddings). Anthropic has no embedding
  model, hence the second provider.
- `MOCK_AI` — when `true`, skips all real model calls and returns canned data.
  See [Mock Mode](#mock-mode).
- `MOCK_REPORT` — which mock report type to return in mock mode (`blood`,
  `diabetes`, `lipid`, `thyroid`, `vitamins`). Defaults to `blood`. Ignored in
  real mode (the type is detected from the actual report).
- `BACKEND_API_URL` — base URL the MCP server resolves relative `/uploads/...`
  paths against. Defaults to `http://127.0.0.1:8001`.

Before running the pipeline for the first time, build the RAG vector store
(one-time — only re-run if you edit/add articles):

```bash
python3 build_vector_store.py
```

This reads every article in `articles/<type>/`, chunks it, embeds each chunk
(Google Gemini), tags it with its report type, and writes `vector_store.json`
(gitignored — regenerate locally). Note: changing the embedding model changes
the vector dimension and requires a full rebuild.

## Running the API

```bash
uvicorn main:app --port 8001
```

> **Do not use `--reload` for real-mode runs** — it can restart the process
> mid-request during a long LLM call and discard in-progress work.

This single process serves the REST API (`/analyze-report`, `/upload`), the
uploaded-image static files (`/uploads/...`), and the MCP server (`/mcp`).

You can also run the pipeline directly from the command line:

```bash
python3 pipeline.py                  # runs against sample_report.png
python3 pipeline.py path/to/file.pdf # runs against any image or PDF
```

This prints each section (report type, categorized findings with status,
severity, and range provenance; structured advice; disclaimer) and any skipped
pages.

> Want to test without real LLM calls? Set `MOCK_AI=true` in `.env` — see
> [Mock Mode](#mock-mode).

## Pipeline Walkthrough

The entire pipeline is one function: `analyze_report(file_path, sex=None)` in
[pipeline.py](pipeline.py), called by the FastAPI endpoint, the MCP tool, and
the CLI — a single source of truth. Simplified:

```python
def analyze_report(file_path, sex=None):
    # Stage 1: vision extraction (PDF pages merged; bad pages skipped; sex read if present)
    biomarkers, skipped_pages, report_sex = _extract_biomarkers_from_pdf(file_path) \
        if file_path.endswith(".pdf") else (*extract_biomarkers(file_path), [])
    effective_sex = report_sex or sex          # report sex -> caller sex -> general

    biomarkers = resolve_biomarkers(biomarkers)        # normalize names

    # Stages 2-3: group markers by type; split into full sections vs. isolated lone markers
    groups = group_markers_by_type(biomarkers)
    sections = []
    for report_type, markers in groups.items():
        if len(markers) >= SECTION_THRESHOLD:
            sections.append(_build_section(markers, report_type, sex=effective_sex))
        else:
            ...pool into isolated...
    # (lone markers -> one _build_isolated_section; nothing recognized -> unknown section)

    return {"sections": sections, "skipped_pages": skipped_pages}
```

Each `_build_section` runs Stages 4–5 (categorize + type-filtered RAG advice) and
attaches a guaranteed per-section disclaimer.

## Stage 1 — Vision Extraction

**File:** [pipeline.py](pipeline.py) → `extract_biomarkers()`,
`_extract_biomarkers_from_pdf()`; [pdf_utils.py](pdf_utils.py)

A **multimodal** call: the report image is base64-encoded and sent as an
Anthropic **image content block**. PDFs are first rendered to page images
(PyMuPDF); every page is extracted and merged into one result, and a page that
fails extraction is skipped and its number reported (rather than failing the
whole report). The prompt also asks for the patient's sex, accepted only if it
is clearly `"male"`/`"female"` (else treated as unknown — never guessed).

The prompt requests strict JSON: a `sex` field plus one nested object per
marker (`value`, `unit` as printed or `""`, `printed_range` as printed or
`null`). Output is parsed via `json_utils.extract_json`, which tolerates the
markdown code fences models often add despite being told not to. A parse failure
counts as an error and triggers retry/fallback.

## Stage 2 — Detection, Normalization & Categorization

**Files:** [name_resolver.py](name_resolver.py), [detector.py](detector.py),
[categorize.py](categorize.py), [report_data.json](report_data.json)

This stage is **deliberately not AI**:

1. **Name normalization** — extracted names are resolved to canonical names via
   a per-marker alias map plus case/whitespace/punctuation normalization (e.g.
   `Hb`, `HGB`, `Haemoglobin` → `Hemoglobin`). Unknown names pass through
   unchanged rather than being mis-mapped.
2. **Grouping by type** — each marker's report type is looked up from
   `report_data.json` and markers are grouped per type (see Stage 3).
3. **Categorization** — each value is judged against that type's reference data.
   Three marker kinds are supported: **range** (Low/Normal/High), **direction**
   (one-sided, e.g. Vitamin D), and **bands** (named tiers, e.g. HbA1c's
   Prediabetes/Diabetes). Every finding carries a uniform `status` plus a
   `severity` (`normal` / `attention` / `critical` / `unassessed`). The report's
   own printed range takes precedence over the built-in range for range markers
   (with a `range_source` provenance field); where no printed range exists,
   sex-specific variants apply when the sex is known.

## Stage 3 — Grouping into Sections

**File:** [pipeline.py](pipeline.py)

Because one upload can mix report types, markers are grouped by type and each
group is handled on its own:

- A type with at least `SECTION_THRESHOLD` (2) markers becomes a **full
  section** — categorized, advised, and given its own disclaimer.
- Lone markers (below the threshold) are pooled into a single **"isolated"**
  section: still categorized (so status/severity show), but framed as
  low-confidence ("these appeared on their own, may be incidental or misread,
  see a doctor") rather than presented as a confident typed report. This avoids
  manufacturing an authoritative section from a single possibly-misread marker.
- If nothing is recognized at all, a single honest **"unknown"** section is
  returned.

The result is always a list of sections, whether the report is single-type or
mixed — one consistent shape for consumers.

## Stage 4 & 5 — Type-Filtered RAG

**Files:** [load_articles.py](load_articles.py), [chunker.py](chunker.py),
[embedder.py](embedder.py), [build_vector_store.py](build_vector_store.py),
[retriever.py](retriever.py), [advisor.py](advisor.py)

### Building the knowledge base (offline, one-time)

`load_articles.py` reads every `.md` in `articles/<type>/`, tagging each with
its report type (the subfolder name). `chunker.py` splits each into overlapping
word chunks (60 words / 15 overlap). `embedder.py` embeds each chunk via Google
Gemini. Every `{article, type, chunk_index, text, embedding}` record is written
to `vector_store.json` (currently ~201 chunks across 21 articles).

### Retrieval (type-filtered)

`retrieve_relevant_chunks(query, store, top_k, report_type)` embeds the query,
**hard-filters candidates to the given report type**, then cosine-ranks and
returns the top-k. If no chunk matches the type, it returns nothing and the
caller falls back to generic guidance — a lipid query can never surface a
thyroid article.

### Grounded structured generation

`generate_advice()` filters findings to `severity == "attention"` (or higher),
retrieves per-finding context (type-filtered), and asks Claude for structured
JSON:

```
Using ONLY the reference information above, write brief, general, educational
guidance. Do not diagnose. Do not recommend medications or dosages.
Respond as: {"summary": "...", "findings": [{"name": "...", "advice": "..."}]}
```

Parsed with `json_utils.extract_json`; on failure it **degrades to
summary-only** (the model's raw text becomes the summary) so advice is never
lost. (The "isolated" section is categorized but given a fixed honest summary
rather than generated advice.)

## Reference Data Model

All per-type data lives in [report_data.json](report_data.json) (data, not
code), keyed by report type. Each type has a `display_name`, `category`
(`numeric` / future `narrative`), `signature_markers` (for detection), and
`ranges`. Each marker declares a `kind`:

```json
"Hemoglobin": { "kind": "range", "min": 13.0, "max": 17.0, "unit": "g/dL",
                "critical_low": 7.0, "critical_high": 20.0,
                "aliases": ["Hb", "HGB", "Haemoglobin"],
                "variants": { "male":   {"min":13.5,"max":17.5},
                              "female": {"min":12.0,"max":15.5} } }

"HbA1c": { "kind": "bands", "unit": "%", "aliases": ["A1c", "HBA1C"],
           "bands": [ {"max":5.7,"label":"Normal","severity":"normal"},
                      {"min":5.7,"max":6.5,"label":"Prediabetes","severity":"attention"},
                      {"min":6.5,"label":"Diabetes","severity":"attention"} ] }
```

Top-level `_default_disclaimer` and `_critical_disclaimer` provide shared
disclaimer text (types may override per-type). **These values — ranges, variant
ranges, band thresholds, and critical thresholds — are illustrative and pending
medical review.**

## Sex-Specific Ranges

**Files:** [categorize.py](categorize.py), [report_data.json](report_data.json)

A few markers have genuinely sex-dependent normal ranges (Hemoglobin,
Hematocrit, RBC Count). Those markers carry a `variants` block with `male` and
`female` ranges; the top-level `min`/`max` remain the default. The sex used is
chosen by precedence: **the sex stated on the report → a caller-supplied sex →
otherwise the general range** (never guessed). Only `"male"`/`"female"` are
accepted; anything else falls back to the general range. The variant numbers are
illustrative and pending medical review.

> Note: a printed range on the report still takes precedence over sex variants
> for range markers (the report's own range is the most specific). Sex variants
> apply when no usable printed range is present.

## Safety Framing: Disclaimers & Critical Values

- **Guaranteed disclaimer** — every section carries a `disclaimer` attached in
  code (not left to the model), so it's present on every path including the
  degrade-to-summary, isolated, and unknown cases.
- **Critical values** — a value past an optional `critical_low`/`critical_high`
  (range markers) or in a band marked `critical` gets `severity: "critical"`,
  which escalates that section to a stronger `_critical_disclaimer`. Thresholds
  are defined only where reasonably established and calibrated conservatively to
  avoid false alarms; messaging stays calm and non-diagnostic.

## Narrative Reports (planned)

Narrative/text-based reports (e.g. radiology, pathology) are **not yet
supported** — only numeric reports are. A design decision has been recorded for
how they will be handled when built: narrative findings will be **explained in
plain language but not rated** (no status/severity) — whether a finding is
concerning is left to a doctor, since judging free-text clinical significance is
exactly the kind of interpretation this tool avoids. This decision is
**proposed, pending confirmation in the medical review**, and gates the
narrative work. See `DECISIONS.md` (HRA-21).

## Resilience: Retries & Multi-Model Fallback

Both LLM call sites — vision ([pipeline.py](pipeline.py)) and text
([advisor.py](advisor.py)) — iterate an ordered model list:

```python
VISION_MODELS = ["claude-sonnet-4-5", "claude-haiku-4-5"]
TEXT_MODELS   = ["claude-sonnet-4-5", "claude-haiku-4-5"]
```

Each model is retried a few times (with linear backoff) before falling through
to the next. The embedding call ([embedder.py](embedder.py)) has its own retry
loop (no fallback model — a known gap, since only one embedding model is used).

## Mock Mode

Set `MOCK_AI=true` in `.env` to bypass every real model call. `MOCK_REPORT`
selects which type to simulate. Extraction returns that type's canned
biomarkers (sex `None` → general ranges) and advice generation returns its
canned structured advice (both from [mock_data.py](mock_data.py), where each
type owns its biomarkers *and* advice together). Grouping, categorization,
sectioning, disclaimer, and result assembly all run for real, so mock mode
exercises the full structure at zero cost — and mock output has the same shape
as real output by construction.

## API Reference

**File:** [main.py](main.py)

### `GET /`
Health check.

### `POST /analyze-report`
`multipart/form-data` with a single `file` field — an **image or a PDF**. The
file is written to a temp file, run through `analyze_report()`, and the temp
file is deleted afterward regardless of outcome.

**Response body (shape):**

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
      "advice": {
        "summary": "…overall note ending with a doctor-consult reminder…",
        "findings": [ { "name": "Hemoglobin", "advice": "…" } ]
      },
      "disclaimer": "This analysis is educational only and is not a medical diagnosis…"
    }
  ],
  "skipped_pages": []
}
```

A mixed report returns multiple sections (one per detected type). Lone markers
appear under a `"report_type": "isolated"` section. An unrecognized report
returns a single `"report_type": "unknown"` section with empty findings and an
honest unsupported message in `advice`.

**Error responses:** `400` (file is not an image or PDF), `500` (analysis
failed after exhausting fallbacks). CORS is wide open (`allow_origins=["*"]`)
for local development — restrict before any deployment.

### `POST /upload`
Saves an uploaded image/PDF to `uploads/` under a UUID filename and returns
`{ "url": "/uploads/<uuid>.<ext>" }`, so a client can hand the MCP server a
stable fetchable URL rather than raw bytes.

## MCP Server & ChatGPT Integration

**File:** [mcp_server/server.py](mcp_server/server.py)

The pipeline is exposed as a tool over the **Model Context Protocol (MCP)**
using [FastMCP](https://github.com/jlowin/fastmcp), so an MCP-compatible client
(ChatGPT, Claude, etc.) can call it during a conversation:

```python
@mcp.tool
def analyze_blood_report(file_url: str) -> dict:
    ...
```

The tool takes a `file_url` (image **or** PDF); a relative `/uploads/...` path
is resolved against `BACKEND_API_URL`, the file is fetched with `httpx` (its
extension preserved so PDFs route correctly), run through the same
`analyze_report()` pipeline, and the result returned (the `sections` shape).
The FastMCP app is mounted into the main FastAPI app so one
process/port/tunnel covers the REST API, static uploads, and MCP.

> **Note:** the tool is still named `analyze_blood_report` for backward
> compatibility (renaming it requires recreating the ChatGPT connector, which
> can cache the old schema). Its docstring reflects that it accepts images or
> PDFs of health reports and returns the multi-section result. A broader
> blood → health rename (repo, tool name) is tracked as future work.

### Exposing it to a remote client (ChatGPT) via ngrok

ChatGPT needs a public HTTPS URL for both the MCP endpoint and any fetched
image. For local dev, [ngrok](https://ngrok.com) tunnels one:

```bash
uvicorn main:app --port 8001
ngrok http 8001
```

Register `https://<ngrok-subdomain>.ngrok-free.dev/mcp` as the connector's MCP
URL. (Free ngrok URLs are random and change per session. ngrok's free tier
allows only one tunnel at a time — a reason the MCP server is mounted into the
main app rather than run separately.)

## File-by-File Reference

| File | Role |
|---|---|
| [main.py](main.py) | FastAPI app, CORS, `/analyze-report` + `/upload`, mounts MCP at `/mcp` |
| [mcp_server/server.py](mcp_server/server.py) | FastMCP server exposing the analyze tool |
| [pipeline.py](pipeline.py) | `analyze_report()` orchestration; vision extraction; PDF handling; sectioning; CLI |
| [pdf_utils.py](pdf_utils.py) | Renders PDF pages to images (PyMuPDF) |
| [name_resolver.py](name_resolver.py) | Normalizes lab names → canonical (alias map) |
| [detector.py](detector.py) | Report-type detection; marker grouping; disclaimer accessor |
| [categorize.py](categorize.py) | Rule-based status + severity (range / direction / bands), sex-aware |
| [report_data.json](report_data.json) | Per-type markers, ranges, variants, aliases, disclaimers, critical thresholds |
| [load_articles.py](load_articles.py) | Loads articles from type subfolders, tagged by type |
| [chunker.py](chunker.py) | Word-based overlapping chunker |
| [embedder.py](embedder.py) | `embed_text()` — text → embedding (Google Gemini), with retry |
| [build_vector_store.py](build_vector_store.py) | One-time: chunk + embed + type-tag → `vector_store.json` |
| [retriever.py](retriever.py) | Type-filtered cosine similarity search |
| [advisor.py](advisor.py) | Structured grounded advice (Anthropic), with fallback |
| [json_utils.py](json_utils.py) | Fence-tolerant JSON parsing (shared) |
| [mock_data.py](mock_data.py) | Per-type canned biomarkers + advice for `MOCK_AI` |
| [articles/](articles/) | RAG knowledge base — 21 articles in type subfolders |
| [uploads/](uploads/) | Uploaded files (gitignored) |
| [sample_report.png](sample_report.png) | Synthetic sample report |
| [playground.py](playground.py) | Scratch file |

## Extending the Knowledge Base

To add coverage for a new condition within an existing report type:

1. Add a new `.md` file to the relevant `articles/<type>/` subfolder with
   general, factual, non-diagnostic guidance. Keep the AI-drafted content
   pending-review discipline until a professional signs off.
2. Add/adjust the marker (and any aliases, variants, critical thresholds) in
   [report_data.json](report_data.json) under that type.
3. Re-run `python3 build_vector_store.py` to re-chunk, re-embed, and re-tag
   everything (a full rebuild, not incremental).

To add a whole new report type, add a new top-level entry to
`report_data.json` (with `display_name`, `category`, `signature_markers`,
`ranges`) and a new `articles/<type>/` subfolder, then rebuild the store.

## Roadmap

- [x] Vision-based extraction (multimodal LLM), images **and PDFs**
- [x] Multi-report-type support (blood, diabetes, lipid, thyroid, vitamins)
- [x] Report-type detection + name normalization
- [x] Rule-based categorization with graded severity + critical values
- [x] On-report unit/printed-range capture with precedence + provenance
- [x] Sex-specific reference ranges (report → caller → general)
- [x] Type-filtered RAG (chunking, Gemini embeddings, filtered retrieval)
- [x] Structured per-finding advice with degrade-to-summary fallback
- [x] Guaranteed disclaimers (code-enforced) with critical escalation
- [x] Mixed-report support (multiple types per upload) with isolated-marker handling
- [x] Graceful PDF page skipping (partial success)
- [x] Multi-provider architecture (Anthropic + Gemini); retry + model fallback
- [x] FastAPI service + MCP tool (images/PDFs, sections result)
- [x] Design decision for narrative handling (explain-not-rate) — recorded, pending review
- [ ] **Medical review** of articles, ranges, variants, and critical thresholds
      by a qualified professional (the key safety gate; also confirms the
      narrative-handling decision)
- [ ] Narrative/radiology report support (extraction + safe framing) — gated on review
- [ ] Reconnect the frontend to the current `sections` response shape
- [ ] Evaluation harness for retrieval/generation quality across types
- [ ] Blood → Health rename pass (repo, MCP tool name)
- [ ] Module-boundary refactor (split pipeline.py; relocate helpers)
- [ ] MCP authentication (currently No Auth — dev only)
- [ ] Restrict CORS; real deployment behind a stable URL
- [ ] Automated tests
- [ ] Refresh remaining core docs (ARCHITECTURE, MASTER_CONTEXT, etc.)

## Disclaimer

This project generates general, educational health information only. It does
not diagnose conditions, recommend medications or dosages, and is not a
substitute for professional medical advice. Its medical content is currently
AI-drafted and pending professional review. Always consult a licensed doctor to
interpret real lab results.
