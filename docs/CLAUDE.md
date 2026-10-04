# CLAUDE.md — Start Here

The entry point for any AI assistant (or human) picking up this project. Read this
first, then `CURRENT_STATUS.md`, then the rest in the order below.

---

## What this project is

A hands-on **AI-engineering learning project**. The developer (Arpit — ~10 years of
general software experience, deliberately new to AI engineering) is building a real,
working AI product end-to-end — not a tutorial toy — to become a production-ready AI
integration engineer. Learning-by-building was chosen over isolated tutorials on
purpose.

**The product — "Health Report Analyzer":** upload a photo or PDF of a lab report; a
vision-language model extracts biomarker name/value/unit/printed-range (and patient
sex if shown); plain rule-based code normalizes names, groups markers by report type,
and tags each value by status + severity against reference data; and a type-filtered
RAG pipeline generates grounded, **non-diagnostic** health guidance from a curated
knowledge base. It currently supports **five report types** — blood (CBC), diabetes,
lipid, thyroid, vitamins — and handles a single upload that mixes several types. The
same capability is exposed two ways: a FastAPI HTTP API, and an **MCP tool** callable
by AI assistants.

> The project began as a blood-only "Blood Report Analyser" and was generalized into
> the multi-type Health Report Analyzer. The blood *report type* still exists; only
> the project name changed.

**This is not a medical device.** All guidance must stay general, educational, and
non-diagnostic, and must always recommend consulting a licensed doctor.

> **Medical content is AI-drafted and pending review.** The knowledge-base articles,
> reference ranges, sex variants, and critical thresholds were drafted by an AI and
> have **not** been reviewed by a medical professional. They are illustrative, not
> authoritative. A doctor review is the key outstanding safety gate.

---

## Read in this order

1. `CLAUDE.md` — this file (how to operate here).
2. `CURRENT_STATUS.md` — where things stand right now; **read before doing anything**.
3. `MASTER_CONTEXT.md` — full project context, stack, structure, background.
4. `ARCHITECTURE.md` — how the system fits together and what calls what.
5. `docs/DECISIONS.md` — why things were built this way; check before proposing changes.
6. `docs/SPRINT_BOARD.md` — what's done and what's next (the live backlog).
7. `PROJECT_RULES.md` — the non-negotiables (safety, conventions, workflow).
8. `LEARNING_JOURNAL.md` — chronological record of concepts learned and problems solved.

---

## The stack (short version)

| Part | Tech |
|---|---|
| Backend | Python, FastAPI, Uvicorn |
| Vision + text LLM | Anthropic Claude (`claude-sonnet-4-5`, `claude-haiku-4-5` fallback) |
| Embeddings | Google Gemini (`gemini-embedding-2-preview`) — Anthropic has no embedding model |
| Vector store | Local JSON file (`vector_store.json`), cosine search via NumPy |
| Reference data | `data/report_data.json` |
| MCP | FastMCP, mounted inside the FastAPI app |

Two providers because Anthropic offers no embedding model. Model IDs are volatile
config, not fixed architecture.

---

## Project layout

Library code is organized into packages; entry-point scripts stay at the root.

```
(root)   main.py, cli.py, build_vector_store.py, playground.py
core/    extractor, detector, categorize, advisor, pipeline
rag/     load_articles, chunker, embedder, retriever
data/    report_data.json, disclaimer, mock_data
utils/   json_utils, pdf_utils
mcp_server/   server.py
articles/     RAG knowledge base (21 articles in type subfolders)
docs/         DECISIONS.md, SPRINT_BOARD.md
```

The whole pipeline is one function: `core.pipeline.analyze_report(file_path, sex=None)`,
called identically by the CLI, the FastAPI endpoint, and the MCP tool. It returns
`{sections: [...], skipped_pages: [...]}` — one section per detected report type (plus a
low-confidence "isolated" section for lone markers, or an "unknown" section if nothing
is recognized).

---

## How to behave when working here

- **Check status first.** Read `CURRENT_STATUS.md` and `docs/DECISIONS.md` before
  starting; don't redo completed work.
- **Preserve architectural decisions** unless there's a strong, explicit reason to
  revisit. Significant ones are logged in `docs/DECISIONS.md`.
- **Codebase is the source of truth.** If docs and code disagree, the code wins; fix
  the docs to match.
- **Never invent missing information.** If something isn't known from the code or the
  record, say so plainly rather than guessing.
- **Keep the safety framing sacred:** non-diagnostic, no medications/dosages, always a
  doctor-consult disclaimer, advice grounded only in retrieved context. The disclaimer
  is guaranteed in code, not left to the model.
- **Keep categorization rule-based** (`core/categorize.py` + `data/report_data.json`) —
  don't move it into an LLM (DEC-003).
- **Resilience on every AI call** (retry + multi-model fallback + timeout + defensive
  validation) — DEC-011.
- **Update the docs you affect** rather than letting them drift.

---

## Working style (established with Arpit)

- **One step at a time.** Don't batch many unconfirmed steps. But don't over-split a
  single coherent change into artificial micro-steps either.
- **Don't test after every tiny change** — build a coherent piece, then verify once
  (prefer `MOCK_AI=true` for structure/plumbing before spending real quota).
- **Explain AI concepts from a beginner's angle** (plain language, minimal jargon) —
  but don't re-explain general software basics; Arpit is experienced there.
- **Keep code clean and readable** — real modules hold reusable logic; scratch goes in
  `playground.py`; one responsibility per module; no orphan/dead code left behind.
- **Give full functions when editing** (not fragments to stitch), and name the file.
- **Be critical and honest.** Flag risks, over-engineering, and when a step isn't
  needed. Challenge decisions from both sides on consequential calls.
- **Maintain `LEARNING_JOURNAL.md`** with AI/Python/React lessons as they come up.

---

## Fast commands

```bash
source venv/bin/activate              # from project root; venv does NOT persist across sessions
# (if the project folder was renamed/moved, the venv breaks — recreate it)
python3 build_vector_store.py         # one-time / after editing articles -> writes vector_store.json
MOCK_AI=true python3 cli.py           # analyze sample_report.png, no real AI calls
python3 cli.py path/to/report.pdf     # analyze any image or PDF (real mode)
uvicorn main:app --port 8001          # run API + mounted MCP. NO --reload in real mode.
```

---

## Environment gotchas that WILL bite (from real experience)

- **Locked-down company Linux machine.** `sudo`, `apt`, `curl` are blocked; `wget`,
  `git` work. Route around blocked tools (e.g. create a venv `--without-pip`, then
  `wget` get-pip.py).
- **The venv does not persist** across sessions, and **breaks if the project folder is
  renamed/moved** (it bakes in its absolute path) — recreate it when that happens. When
  something "should just work" and doesn't, run `which python3` first.
- **Run from the project root** — `report_data.json` is resolved relative to the working
  directory.
- **No `requirements.txt` yet** — a fresh venv needs a manual `pip install` of the deps
  (fastapi, uvicorn, anthropic, google-genai, python-dotenv, numpy, pillow, fastmcp,
  httpx, pymupdf). Adding a requirements file is a tracked follow-up.
- **Never `uvicorn --reload` in real mode** — it restarts mid-request and discards
  in-progress work.
- **Two providers, two keys:** `ANTHROPIC_API_KEY` (Claude) and `GEMINI_API_KEY`
  (embeddings), plus `MOCK_AI` and optional `MOCK_REPORT`, in `.env`.

---

## Current objective (as of last recorded state)

First end-to-end draft is complete and the codebase has been refactored (module split,
package reorg) and renamed (blood → health). The near-term work is: finish the docs
refresh, prepare the medical-review package for a doctor (the key safety gate, which
also unblocks narrative-report support), and reconnect the frontend to the current
`sections` response shape. Narrative/radiology support (HRA-22/23) is deliberately
last and gated on the medical review. See `CURRENT_STATUS.md` for the authoritative,
most-current picture.
