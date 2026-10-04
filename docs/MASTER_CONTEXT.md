# MASTER_CONTEXT.md

The single source of truth for full project context. If you read only one document,
read this one. For the live "where are we" snapshot see `CURRENT_STATUS.md`; for how
the pieces fit see `ARCHITECTURE.md`; for why choices were made see `docs/DECISIONS.md`.

Legend: ✅ current/verified · ⚠️ caveat · ❓ unknown/not-done.

---

## 1. Project overview

A hands-on AI-engineering learning project: build a real, working AI product
end-to-end (not a toy) to develop production-relevant skills. The product is a
**Health Report Analyzer** — upload a lab report (image or PDF), get back
structured, grounded, non-diagnostic educational guidance.

It began as a blood-only "Blood Report Analyser" and was generalized into a
multi-report-type tool. It currently supports five report types: **blood (CBC),
diabetes, lipid, thyroid, vitamins**, and handles uploads that mix several types.

## 2. Background & why it exists

✅ Arpit is a developer with ~10 years of general experience, deliberately a beginner
in AI engineering. Goal: become a production-ready AI integration engineer, learned by
building a real project rather than isolated tutorials. There was no external
"customer" — the purpose is skill development, with lab-report analysis chosen as a
rich, realistic domain (vision, structured output, deterministic logic, RAG, MCP,
multi-provider, resilience).

Evolution:
```
Blood-only analyser (vision + rule-based categorize + RAG advice + FastAPI + MCP)
      ↓  generalized
Health Report Analyzer — five report types, mixed-report handling
      ↓  hardened & cleaned
Structured output, guaranteed disclaimers, critical values, sex-specific ranges,
module refactor, package reorg, blood→health rename
      ↓  planned, gated on medical review
Narrative/radiology report support
```

## 3. Goals

- Learn AI engineering hands-on: vision LLMs, structured output, embeddings, chunking,
  vector search, type-filtered RAG, prompt engineering, resilience/fallback, MCP.
- Build something genuinely functional end-to-end.
- Practice production habits: clean modular code, git discipline (Conventional
  Commits), documentation, and safety/disclaimer-conscious design for a
  health-adjacent product.
- Keep a living `LEARNING_JOURNAL.md`.

## 4. Non-goals

- **Not** a real medical diagnostic product; all advice is general, educational,
  non-diagnostic, with a mandatory doctor-consult disclaimer.
- Not (yet) for real end-users beyond Arpit's own testing.
- Automated testing (pytest) deliberately deferred during the learning phase (DEC-007).

## 5. Current capabilities

**Functional:**
- Accept a lab report as an image or a PDF (multi-page PDFs merged; an unreadable page
  is skipped and reported).
- Extract biomarker name/value/unit/printed-range via a vision LLM as JSON; also read
  the patient's sex if the report shows it.
- Normalize lab-specific marker names to canonical names (alias map).
- Detect report type(s) and group markers; handle a single upload that mixes types,
  producing one **section** per type (plus a low-confidence "isolated" section for
  lone markers).
- Categorize each value rule-based: status (High/Low/Normal or a named band) + a
  uniform severity (normal / attention / critical / unassessed). Three marker kinds:
  range, direction (one-sided), bands (named tiers). Sex-specific ranges where
  established.
- Prefer the report's own printed range over built-in ranges (with provenance), and
  escalate a stronger disclaimer when a critical value is present.
- For abnormal findings, type-filtered RAG retrieval + grounded, structured,
  per-finding advice.
- Guaranteed disclaimer on every result (code-enforced).
- `MOCK_AI` mode that bypasses all real AI calls with canned per-type data.
- Exposed via FastAPI HTTP API and an MCP tool.

**Technical:** Python backend; Claude (vision + text) via the Anthropic SDK; Google
Gemini embeddings via `google-genai`; a local-JSON vector store (no vector DB);
resilience via retry + multi-model fallback; MCP via FastMCP mounted in the FastAPI app.

## 6. Users / consumers

- **Primary user:** Arpit, testing locally.
- **Consumer surfaces:** the FastAPI HTTP API (and, separately, a React frontend in its
  own repo — not yet reconnected to the current response shape); and an MCP-compatible
  AI assistant via the `analyze_health_report` tool (not currently connected to ChatGPT).

## 7. Technology stack

| Technology | Why | Where | Notes |
|---|---|---|---|
| Python | Backend language | everywhere | run from the project root |
| FastAPI | Web framework | `main.py` | common choice for AI backends |
| Uvicorn | ASGI server | runs `main:app` | **never `--reload` in real mode** |
| Anthropic SDK (Claude) | Vision + text LLM | `core/extractor.py`, `core/advisor.py` | `max_tokens` required; image as a base64 content block; `messages` API |
| google-genai (Gemini) | Embeddings | `rag/embedder.py` | Anthropic has no embedding model; 3072-dim |
| NumPy | Cosine similarity | `rag/retriever.py` | vector math for retrieval |
| PyMuPDF | PDF → images | `utils/pdf_utils.py` | no system deps; installs clean on the locked-down machine |
| python-dotenv | Secrets/config from `.env` | throughout | `.env` + `.gitignore` |
| FastMCP | MCP server | `mcp_server/server.py` | decorator-based `@mcp.tool`; mounted in FastAPI |
| httpx | HTTP client | `mcp_server/server.py` | MCP tool fetches the file from a URL |
| ngrok | Public tunnel (dev) | exposing API+MCP for a remote client | free tier: one tunnel at a time |
| Git / GitHub | Version control | repo `health-report-analyzer` | Conventional Commits |

> Model IDs are volatile free-/paid-tier config, not fixed architecture.

## 8. Project structure

```
health-report-analyzer/
├── main.py                 # FastAPI app: /analyze-report, /upload; mounts MCP at /mcp
├── cli.py                  # command-line runner (python3 cli.py [file])
├── build_vector_store.py   # one-time: chunk + embed + type-tag articles -> vector_store.json
├── playground.py           # scratch file (not part of the pipeline)
├── core/
│   ├── pipeline.py          # analyze_report(): orchestration, grouping, sectioning
│   ├── extractor.py         # vision + PDF extraction (Claude)
│   ├── detector.py          # report-type detection + marker grouping
│   ├── categorize.py        # rule-based status + severity (range/direction/bands), sex-aware
│   └── advisor.py           # structured grounded advice (Claude) + model fallback
├── rag/
│   ├── load_articles.py     # reads articles/<type>/*.md, tagged by type
│   ├── chunker.py           # overlapping word chunks
│   ├── embedder.py          # text -> embedding (Gemini), retry (no fallback model)
│   └── retriever.py         # cosine search, hard-filtered by report type
├── data/
│   ├── report_data.json     # per-type markers, ranges, variants, aliases, disclaimers, critical thresholds
│   ├── disclaimer.py        # disclaimer lookup (default + per-type + critical)
│   └── mock_data.py         # per-type canned biomarkers + advice for MOCK_AI
├── utils/
│   ├── json_utils.py        # fence-tolerant JSON parsing (shared)
│   └── pdf_utils.py         # PDF pages -> images (PyMuPDF)
├── mcp_server/
│   └── server.py            # FastMCP tool analyze_health_report(file_url)
├── articles/                # 21 knowledge-base articles in type subfolders (blood/, lipid/, ...)
├── uploads/                 # runtime uploads (gitignored)
├── vector_store.json        # generated embeddings (gitignored; regenerable)
├── sample_report.png        # synthetic sample report
├── CLAUDE.md, CURRENT_STATUS.md, MASTER_CONTEXT.md, ARCHITECTURE.md,
├── PROJECT_RULES.md, TODO.md, LEARNING_JOURNAL.md, README.md
└── docs/  DECISIONS.md, SPRINT_BOARD.md
```
Entry-point scripts live at the root; library code is in packages (`core`, `rag`,
`data`, `utils`), each with an `__init__.py`. Imports are absolute-from-root
(`core.`, `rag.`, …).

⚠️ `.gitignore` excludes: `venv/`, `.env`, `__pycache__/`, `*.pyc`, `vector_store.json`,
`uploads/`.

## 9. Important components

- **`core/pipeline.py` / `analyze_report()`** — the single reusable entry point
  (extract → resolve names → group by type → section → per-section categorize + RAG
  advice → guaranteed disclaimer). Called by CLI, FastAPI, and MCP.
- **`core/categorize.py`** — deliberately rule-based, not AI (DEC-003). Three marker
  kinds; uniform severity; sex variants; printed-range precedence.
- **`core/detector.py`** — rule-based type detection + grouping markers by type.
- **RAG stack** (`rag/*`) — load → chunk → embed → store; type-filtered cosine retrieval.
- **`core/advisor.py`** — structured grounded advice with model fallback.
- **`data/report_data.json`** — the data behind detection, categorization, disclaimers
  (DEC-020: data, not code).
- **`mock_data.py` + `MOCK_AI`** — full-structure testing without real AI calls.

## 10. Data flow (primary end-to-end)

```
User/AI provides a report (image or PDF; or a URL via MCP)
      ↓ Stage 1 (core/extractor): vision LLM -> {name:{value,unit,printed_range}} + sex
        (PDF: render pages, merge, skip bad pages)
      ↓ normalize names (core... name_resolver), group by report type (core/detector)
      ↓ split into sections: types with >= threshold markers -> full section;
        lone markers -> one "isolated" section
      ↓ per section — Stage 2 (core/categorize): status + severity vs report_data.json
      ↓ per section — Stage 3 (rag/retriever): embed query, cosine search FILTERED to
        the section's type
      ↓ per section — Stage 4 (core/advisor): LLM writes {summary, findings:[{name,advice}]}
        from retrieved context, non-diagnostic
      ↓ guaranteed disclaimer stamped per section (data/disclaimer)
      ↓ returns {sections:[...], skipped_pages:[...]}
```

## 11. APIs / interfaces

✅ FastAPI (`main.py`):
- `GET /` — health check.
- `POST /analyze-report` — multipart image/PDF upload; runs the pipeline; returns the
  sections result, or HTTP 400 (not an image/PDF) / 500 (analysis failed).
- `POST /upload` — saves an image/PDF to `uploads/`, returns `{"url": "/uploads/<uuid>.<ext>"}`.
- `/uploads/...` — static serving.
- `/mcp` — the mounted MCP server.

✅ MCP tool: `analyze_health_report(file_url: str) -> dict` — fetches the file (image or
PDF), runs the same `analyze_report()`, returns the sections result. (Renamed from
`analyze_blood_report`; not currently connected to ChatGPT.)

**Response contract:**
```jsonc
{
  "sections": [
    {
      "report_type": "blood",            // or lipid/thyroid/diabetes/vitamins/isolated/unknown
      "findings": [
        { "kind": "numeric", "name": "Hemoglobin", "value": 10.6, "unit": "g/dL",
          "status": "Low", "severity": "attention",   // normal|attention|critical|unassessed
          "normal_range": "13.0-17.0 g/dL", "printed_range": "13.0-17.0",
          "range_source": "report" }                  // report|data|none
      ],
      "advice": { "summary": "…", "findings": [ { "name": "…", "advice": "…" } ] },
      "disclaimer": "…"                  // guaranteed, code-enforced
    }
  ],
  "skipped_pages": []                    // PDF pages that couldn't be read
}
```

## 12. Data / database

No database. Persistent state:
- `data/report_data.json` — per-type markers, ranges, sex variants, aliases, disclaimers,
  critical thresholds (hand-maintained; **illustrative, pending medical review**).
- `vector_store.json` — flat JSON of `{article, type, chunk_index, text, embedding}`
  (~201 chunks across 21 articles; gitignored; regenerable; 3072-dim Gemini vectors).
- `articles/` — 21 markdown articles in type subfolders.
- `uploads/` — runtime files, UUID-named.

❓ No SQL/NoSQL DB, user accounts, or history storage.

## 13. Infrastructure

- Local only. One `uvicorn main:app --port 8001` process serves API + static + MCP.
- ngrok for temporary public exposure during MCP testing (one tunnel).
- GitHub repo `health-report-analyzer` (the frontend is a separate repo).
- ❓ No CI/CD; minimal logging (`print()` + uvicorn logs).

## 14. Development workflow

Iterative, one coherent step at a time (not micro-steps; not batches of unconfirmed
changes). Real API calls treated as a limited resource: build a layer, then test once;
prefer `MOCK_AI=true` for structure/plumbing. Scratch code in `playground.py`. Clean
modular code, no orphan code. Conventional Commits, scoped per logical change.

## 15. Testing

✅ No automated suite (pytest) — deliberately deferred (DEC-007). Verification to date
is manual: mock-mode runs (all five types, mixed, critical, sex variants), one real PDF
run (blood), and targeted real calls (advisor, retrieval). An evaluation approach for
AI output quality is tracked (HRA-25), not built.

## 16. Deployment

Not deployed. "Deployment" = local `uvicorn` + a temporary ngrok tunnel when external
reachability is needed. Real deployment (hosting, auth, CORS, observability) is future
work.

## 17. Security

- `.env` for secrets (`ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `MOCK_AI`, `MOCK_REPORT`,
  `BACKEND_API_URL`); excluded from git.
- ⚠️ MCP server runs **No Auth** (dev only).
- ⚠️ CORS wide open (dev only).

## 18. Known problems / open items

See `CURRENT_STATUS.md` for the live list. Highlights:
- **Medical review not done** — all AI-drafted medical content is pending a doctor's
  review (the key safety gate; also confirms the narrative decision).
- Frontend not reconnected to the `sections` shape.
- No `requirements.txt`; must run from project root; no MCP auth; no tests.
- Real-mode not re-run since the refactor/rename (logic unchanged).

## 19. Context that's easy to forget

- **Locked-down company Linux laptop:** `sudo`/`apt`/`curl` blocked; `wget`/`git` fine.
- **venv doesn't persist** across sessions and **breaks if the project folder is moved/
  renamed** (bakes in its path) — recreate it; check `which python3` first.
- **Run from the project root** (JSON path is cwd-relative).
- **Two providers, two keys** (Claude + Gemini); embeddings have no fallback model.
- **Never `uvicorn --reload`** in real mode.
- **"blood" is both** a former project name (renamed to "health") *and* a current report
  type (kept) — don't conflate them.
- All scratch/experimental code stays in `playground.py`.

## 20. Pointers

Status → `CURRENT_STATUS.md` · How it fits → `ARCHITECTURE.md` · Why → `docs/DECISIONS.md`
· Backlog → `docs/SPRINT_BOARD.md` · Rules → `PROJECT_RULES.md` · Lessons →
`LEARNING_JOURNAL.md`.
