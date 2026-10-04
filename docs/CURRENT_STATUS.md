# CURRENT_STATUS.md

> Snapshot of where the Health Report Analyzer stands right now. Read this first
> when picking the project back up. For the full picture see `MASTER_CONTEXT.md`,
> for how the system fits together see `ARCHITECTURE.md`, and for the pending-work
> breakdown see `docs/SPRINT_BOARD.md`.

## Overall Status

```
Project:        Health Report Analyzer (formerly Blood Report Analyser)
Stage:          First end-to-end draft complete (numeric engine feature-complete)
Core pipeline:  Working end-to-end — verified in mock mode throughout, and via a
                real PDF run (blood). Supports five report types + mixed reports.
Narrative:      Not built — gated on the medical-review decision (HRA-21/HRA-24).
Production:     Auth, tests, deployment largely not started.
Medical review: NOT yet done — all AI-drafted medical content is pending review.
```

## What the system does (one paragraph)

Upload an image or PDF of a lab report. A vision-language model (Anthropic Claude)
extracts biomarker name/value/unit/printed-range (and the patient's sex if shown);
plain rule-based code normalizes names, groups markers by report type, and
categorizes each value (status + severity) against reference data; a type-filtered
RAG step (Google Gemini embeddings + a local JSON vector store) retrieves grounded
guidance; and Claude generates structured, non-diagnostic, per-finding advice. The
result is a list of per-type **sections**, each with findings, structured advice,
and a guaranteed disclaimer, plus any skipped pages. Exposed via a FastAPI HTTP API
and an MCP tool.

## Completed

**Feature work (HRA-01 through HRA-21):**
- HRA-01 Unified `findings` schema (typed entries with a `kind` discriminator).
- HRA-02 Rule-based report-type detection (signature-marker set intersection).
- HRA-03 PDF support (PyMuPDF page-render → vision), HTTP + MCP paths.
- HRA-04 Resilience guard recorded as a Definition-of-Done item (no new AI calls then).
- HRA-05 Unknown report types short-circuit with an honest unsupported message.
- HRA-06 Five report types (blood, diabetes, lipid, thyroid, vitamins) in
  `report_data.json`; three marker kinds (range / direction / bands); uniform severity.
- HRA-07 Captured on-report units + printed ranges; printed-range precedence; provenance.
- HRA-08 Biomarker name normalization (alias map + case/whitespace), safe pass-through.
- HRA-09 Report-category routing in the pipeline (numeric live; narrative was a stub).
- HRA-10 All five numeric types proven end-to-end in mock mode; unified per-type mock data.
- HRA-11 Knowledge base rebuilt: 21 articles in type subfolders; type-tagged vector store.
- HRA-12 Type-filtered retrieval (hard filter + generic fallback); severity-based advice filter.
- HRA-13 Structured advice `{summary, findings:[{name, advice}]}`; shared fence-tolerant JSON parse.
- HRA-14 Guaranteed per-result disclaimer (code-enforced), with per-type override capability.
- HRA-15 Critical severity + escalated disclaimer (conservatively calibrated).
- HRA-16 Multi-page PDF resilience (skip + report a bad page instead of failing).
- HRA-17 Mixed reports: per-type sections + a low-confidence "isolated" section; result
  shape is now `{sections: [...], skipped_pages}`.
- HRA-18 MCP tool description updated to the current result shape.
- HRA-19 Sex-specific reference ranges (report → caller → general precedence).
- HRA-20 Closed (knowledge-base gaps filled via HRA-11).
- HRA-21 Decision: narrative findings are explained, not rated (proposed, pending review).

**Structural work (post-first-draft):**
- SRP refactor: split overloaded modules — `extractor.py`, `disclaimer.py`, `cli.py`
  pulled out; `pipeline.py` is now pure orchestration; `detector.py` is detection + grouping.
- Folder reorg: library code grouped into `core/`, `rag/`, `data/`, `utils/` packages;
  entry-point scripts (`main.py`, `cli.py`, `build_vector_store.py`) kept at root;
  absolute-from-root imports throughout.
- Blood → Health rename: FastAPI title/status, MCP server name, MCP tool
  (`analyze_blood_report` → `analyze_health_report`). GitHub repo + local folder renamed.
  The blood *report type* was deliberately preserved.

**Provider migration (earlier):**
- Moved off OpenRouter: Claude for vision + text, Google Gemini for embeddings.

## Current Architecture (summary)

One FastAPI process serves the HTTP API, uploaded-file static serving, and a mounted
MCP server. Library code is organized into packages:

```
(root)   main.py, cli.py, build_vector_store.py, playground.py
core/    extractor, detector, categorize, advisor, pipeline
rag/     load_articles, chunker, embedder, retriever
data/    report_data.json, disclaimer, mock_data
utils/   json_utils, pdf_utils
mcp_server/, articles/
```

The whole pipeline is one function, `core.pipeline.analyze_report(file_path, sex=None)`,
called by the CLI, the FastAPI endpoint, and the MCP tool.

## What's verified vs. not

- **Verified:** full pipeline in mock mode (all five types, mixed-report sectioning,
  critical escalation, sex variants, disclaimers); one real PDF end-to-end run (blood);
  structured advice via a real advisor call; type-filtered retrieval via a real query.
- **Not re-verified:** real-mode end-to-end run *since* the folder reorg + rename (no
  logic changed, only structure/names; a real run would confirm). Real vision extraction
  of the non-blood types (mock covers plumbing, not model reading quality). Live MCP via
  ChatGPT (not currently connected).

## Known open items / risks

- **Medical review (the key safety gate):** all AI-drafted medical content — the 21
  articles, reference ranges, sex variants, and critical thresholds — is illustrative and
  **pending review by a qualified doctor**. Must not be treated as authoritative. This
  also confirms the HRA-21 narrative decision and gates narrative support.
- **Frontend:** separate repo, not yet reconnected to the current `sections` response shape.
- **Docs:** being refreshed now (this pass). Some still describe the old system.
- **Run-from-project-root:** `report_data.json` is resolved relative to the working
  directory, so the app must be run from the project root (current workflow already does).
- **No `requirements.txt`:** dependencies are implicit; a fresh venv needs a manual install
  list. Worth adding.
- **MCP auth:** still "No Auth" (dev only). **CORS:** wide open (dev only).
- **No automated tests; no evaluation harness** for AI output quality.

## Immediate next steps

1. Finish the docs refresh (CLAUDE, MASTER_CONTEXT, ARCHITECTURE; light touches to
   README/TODO/PROJECT_RULES).
2. Prepare the medical-review package for the doctor (unblocks narrative).
3. Reconnect the frontend to the `sections` shape.
4. Then, as priorities allow: evaluation approach (HRA-25), `requirements.txt`, and —
   once review clears it — the narrative phase (HRA-22/23).

## Run commands (quick reference)

```bash
source venv/bin/activate              # from the project root; recreate venv if the folder moved
python3 build_vector_store.py         # one-time / after editing articles (real embedding calls)
MOCK_AI=true python3 cli.py           # analyze sample_report.png with no real AI calls
python3 cli.py path/to/report.pdf     # analyze any image or PDF (real mode)
uvicorn main:app --port 8001          # run the API + mounted MCP (no --reload in real mode)
```
