# PROJECT_RULES.md

The non-negotiables for working on the Health Report Analyzer. If a rule and the code
disagree, the code is the source of truth — update the rule to match. For the reasoning
behind many of these, see `docs/DECISIONS.md`.

---

## Safety / AI-output rules (sacred)

- **Non-diagnostic, always.** Generated advice must be general and educational, must
  never diagnose a condition, and must never recommend specific medications or dosages.
- **Always a doctor-consult disclaimer.** Every result carries a disclaimer — and it is
  **guaranteed in code** (stamped in `analyze_report`), not left to the model, so it is
  present even on fallback, isolated, and unknown paths.
- **Grounded advice only.** Advice generation uses ONLY the retrieved knowledge-base
  context ("use only this information"), not the model's general knowledge. This is the
  purpose of the RAG step.
- **No matching article → generic guidance, not fabrication.** When retrieval finds
  nothing for a finding, give generic guidance rather than inventing specifics.
- **Critical values: calm, not alarming.** A critical finding escalates to a stronger
  disclaimer and steers toward prompt medical attention — never diagnosing, never
  alarming. Critical thresholds are defined only where reasonably established and
  calibrated conservatively to avoid false alarms.
- **Medical content is AI-drafted and pending review.** Articles, reference ranges, sex
  variants, and critical thresholds are illustrative until a qualified doctor reviews
  them. Treat them as provisional; do not present them as authoritative.
- **Narrative findings (when built) are explained, not rated** (HRA-21, pending review):
  no status/severity assigned to free-text findings — significance is left to a doctor.

## Architecture rules

- **One pipeline, single source of truth.** `core.pipeline.analyze_report()` is the one
  entry point; the CLI, FastAPI endpoint, and MCP tool all call it rather than
  reimplementing pipeline logic.
- **Categorization stays rule-based** (`core/categorize.py` + `data/report_data.json`),
  never an LLM (DEC-003). Use AI only for genuinely open-ended work (vision extraction,
  advice); use plain code for anything deterministic (normalization, grouping,
  categorization, detection).
- **Resilience on every AI call** (DEC-011): retry + multi-model fallback + timeout +
  defensive response validation on every function that calls an external AI/API. No new
  AI call ships without it.
- **Reference data is data, not code** (DEC-020): markers, ranges, variants, aliases,
  disclaimers, and critical thresholds live in `data/report_data.json`, not hardcoded.
- **Consistent output shape.** `analyze_report` always returns
  `{sections: [...], skipped_pages: [...]}` — the same shape for single- and multi-type
  reports, so consumers never branch on it.
- **Two providers by necessity:** Claude (vision + text), Gemini (embeddings) — Anthropic
  has no embedding model. Model IDs are volatile config, not fixed architecture.

## Code organization rules

- **Single responsibility per module.** Each module has one clear job. Library code lives
  in packages (`core/`, `rag/`, `data/`, `utils/`); entry-point scripts (`main.py`,
  `cli.py`, `build_vector_store.py`) stay at the project root.
- **Absolute-from-root imports** (`core.`, `rag.`, `data.`, `utils.`); each package has an
  `__init__.py`. Run from the project root.
- **No orphan / dead code.** When a change leaves code unused, remove it — but grep the
  whole repo first to confirm it's truly unused before deleting.
- **No ad-hoc test/demo code in real modules.** Exploratory code goes in `playground.py`,
  which is not part of the pipeline. (Genuine entry-point `__main__` blocks are fine.)
- **Shared helpers are shared**, not duplicated (e.g. `utils/json_utils.extract_json`).

## Workflow rules

- **One coherent step at a time** — don't batch many unconfirmed changes, but don't
  over-split a single coherent change into artificial micro-steps either.
- **Build a layer, then test once.** Don't test after every tiny change. Prefer
  `MOCK_AI=true` for verifying structure/plumbing before spending real API quota.
- **Full functions when editing**, and name the file being changed.
- **Be critical and honest** — flag risks, over-engineering, and when a step isn't
  needed; challenge consequential decisions from both sides before committing.
- **Verify imports after structural changes** (`python3 -c "import ..."` + a `MOCK_AI=true`
  run); refactors are where silent breakage hides.

## Git rules

- **Conventional Commits** (`feat:`, `fix:`, `refactor:`, `docs:`, `chore:`), one logical
  change per commit, with a clear body explaining what and why.
- **Review `git status` before staging** — confirm exactly which files are included and
  that no secret or generated file (`.env`, `vector_store.json`, `uploads/`) is staged.
- **`.gitignore`** excludes `venv/`, `.env`, `__pycache__/`, `*.pyc`, `vector_store.json`,
  `uploads/`.
- **Historical records stay historical** — `docs/DECISIONS.md` entries describe what
  happened at the time (including the former "Blood Report Analyser" name); don't rewrite
  history.

## Environment rules

- **Run from the project root** — the `report_data.json` path is working-directory-relative.
- **The venv doesn't persist** across sessions and **breaks if the project folder is
  renamed/moved** (it bakes in its absolute path) — recreate it; check `which python3`
  first when something "should just work" and doesn't.
- **Locked-down dev machine:** `sudo`/`apt`/`curl` are blocked; `wget`/`git` work. Route
  around blocked tools (e.g. create a venv `--without-pip`, then `wget` get-pip.py).
- **Never `uvicorn --reload` in real mode** — it restarts mid-request and discards
  in-progress work.
- **Two keys in `.env`:** `ANTHROPIC_API_KEY`, `GEMINI_API_KEY` (plus `MOCK_AI`,
  `MOCK_REPORT`, `BACKEND_API_URL`).

## Documentation rules

- **Keep the docs you affect in sync.** When behavior changes, update the relevant docs
  (CURRENT_STATUS, MASTER_CONTEXT, ARCHITECTURE, README) in the same breath.
- **Maintain `LEARNING_JOURNAL.md`** with AI/Python/React lessons as they come up
  (beginner-teaching style; not plumbing).
- **Distinguish confirmed from inferred from unknown** in docs; never invent missing
  details (architecture, decisions, schemas, credentials).

## Definition of Done (every change)

- [ ] Safety intact: non-diagnostic, no meds/dosages, guaranteed doctor-consult
      disclaimer, advice grounded only in retrieved context.
- [ ] Works in real mode and (where relevant) `MOCK_AI=true`; mock data shape kept in
      sync if the response shape changed.
- [ ] Categorization stays rule-based; unknown markers flagged, not guessed.
- [ ] Any new AI call has retry + fallback + timeout + defensive validation (DEC-011).
- [ ] No orphan/dead code left; imports verified after structural changes.
- [ ] No secrets or generated artifacts committed; `git status` reviewed.
- [ ] Relevant docs updated, and the *why* recorded in `docs/DECISIONS.md` where it's a
      real decision.
