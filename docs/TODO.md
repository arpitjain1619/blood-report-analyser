# TODO.md

> The authoritative, detailed backlog now lives in **`docs/SPRINT_BOARD.md`** (stories
> HRA-01…HRA-26, with status, acceptance criteria, and dependencies). This file is a
> short, high-level pointer to what's outstanding so you don't have to open the board
> for a quick glance. When they disagree, the sprint board wins.

## Done (high level)

The numeric engine is feature-complete and the codebase has been refactored and renamed.
See `CURRENT_STATUS.md` for the full completed list (HRA-01…HRA-21, the SRP split, the
core/rag/data/utils package reorg, and the blood→health rename).

## Outstanding — the key gate

- [ ] **Medical review of all AI-drafted content** (the key safety gate).
      Have a qualified doctor review: the 21 knowledge-base articles, the reference
      ranges, the sex-specific variants, and the critical-value thresholds (all in
      `data/report_data.json` and `articles/`). This also confirms the narrative-handling
      decision (HRA-21) and unblocks narrative support. Highest priority for anything
      "real." Tracked as HRA-24.

## Outstanding — actionable now (no gate)

- [ ] **Reconnect the frontend** (separate repo) to the current `sections` response
      shape. It still expects the old flat `{report_type, findings, advice}` shape.
- [ ] **Add `requirements.txt`** (and an `.env.example`) so a fresh venv is one command
      instead of a manual install list. The recent venv rebuild made this gap obvious.
- [ ] **Evaluation approach** for AI output quality across report types (HRA-25) — a
      repeatable per-type spot-check, not a full test suite.
- [ ] **Light docs follow-ups:** none of the core docs should now be stale (refreshed:
      CLAUDE, CURRENT_STATUS, MASTER_CONTEXT, ARCHITECTURE, README, PROJECT_RULES). Keep
      them in sync as code changes.

## Outstanding — gated / later

- [ ] **Narrative/radiology support** (HRA-22, HRA-23) — the hardest phase, gated on the
      medical review confirming the HRA-21 "explain, don't rate" decision.
- [ ] **Age-specific reference ranges** — sex variants exist (HRA-19); age-banding was
      deliberately left out and is a future, data-heavy addition.

## Outstanding — production readiness

- [ ] **MCP authentication** — currently "No Auth" (dev only). Needed before any
      longer-lived/public exposure.
- [ ] **Tighten CORS** — currently wide open (`allow_origins=["*"]`), dev only.
- [ ] **Real deployment** — hosting, a stable URL, observability/structured logging.
- [ ] **Automated tests** (pytest) — deliberately deferred during learning (DEC-007),
      tracked as real future work.
- [ ] **Fallback embedding model** — embeddings have retry but no fallback (unlike
      vision/text).

## Known constraints to keep in mind (not tasks)

- Run from the project root (the `report_data.json` path is working-directory-relative).
- The venv breaks if the project folder is renamed/moved — recreate it.
- Locked-down dev machine: `sudo`/`apt`/`curl` blocked; route around them.
- Never run `uvicorn --reload` in real mode.
