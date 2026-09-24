# DECISIONS.md — Engineering Decision Log

> This log records the significant decisions made on the project and _why_, so
> future work (human or AI) doesn't silently undo a deliberate choice. DEC-001…
> DEC-017 come from the build history. Two additional entries (DEC-018, DEC-019)
> at the end capture issues found by reading the actual shipped code — they are
> **open items awaiting a decision**, not decisions already made.

## DEC-001: Choose "Blood Report Analyser" as the learning project

### Status

Accepted

### Context

An AI-engineering learning project needed a concrete build target. A generic "doc chatbot" was initially suggested as a simple RAG-learning exercise.

### Options Considered

1. Generic FAQ/doc chatbot (simple, generic RAG demo)
2. Text summarizer, recipe generator, journaling app, resume matcher, support ticket classifier, text game (other simple starter ideas offered)
3. Blood Report Analyser (proposed by the user)

### Decision

Blood Report Analyser.

### Reason

More personally motivating and realistic; naturally combines multiple real AI-engineering patterns (vision extraction, structured output, deterministic logic, RAG) rather than being a single-concept toy.

### Consequences

#### Positive

- Richer, more realistic multi-part architecture to learn from.
- Personally motivating for the user.

#### Negative

- Health-adjacent domain requires extra care around safety/disclaimer framing (addressed via non-diagnostic language requirements throughout).

### Related Components

Entire project.

---

## DEC-002: Use RAG even where not strictly technically necessary

### Status

Accepted

### Context

The initial blood-report design only needed a small, fixed reference chart for categorization — too small/structured to require semantic search (RAG). This was explicitly explained to the user as a case where RAG doesn't naturally apply.

### Options Considered

1. Skip RAG entirely; use only the reference chart (technically sufficient).
2. Extend the project's knowledge to include a genuine unstructured-document RAG use case, even though not strictly required by the core categorization task.

### Decision

Option 2 — extend scope specifically to include RAG, by adding a knowledge base of 14 educational articles (one per abnormal biomarker condition) for the advice-generation step.

### Reason

Explicit user request: "Since, we are in a learning phase, we should use 'chunking' concept for hands-on" (and, earlier, an explicit statement that RAG must be included even if the project idea needed to change to accommodate it).

### Consequences

#### Positive

- Real hands-on RAG experience (chunking, embeddings, vector store, retrieval) rather than skipping it.
- Resulting hybrid architecture (structured lookup + RAG) mirrors a genuinely common real-world pattern.

#### Negative

- Added complexity/scope beyond what the core problem strictly required.

### Related Components

`articles/`, `chunker.py`, `embedder.py`, `build_vector_store.py`, `retriever.py`, `advisor.py`.

---

## DEC-003: Categorization logic is plain Python, not an AI call

### Status

Accepted

### Context

Needed to decide how to tag each biomarker value as High/Low/Normal.

### Options Considered

1. Ask an LLM to categorize each value.
2. Plain rule-based Python comparison against a reference range.

### Decision

Option 2 — plain Python.

### Reason

Comparing a number against a range is deterministic (one correct answer every time); an LLM call would be slower, cost tokens, and introduce unnecessary risk of error on a task plain code solves reliably. General principle established: use AI for judgment/reasoning/language tasks without a single correct programmatic answer; use plain code for deterministic logic.

### Consequences

#### Positive

- Instant, free, reliable, unit-testable (in principle) logic.

#### Negative

- None significant identified.

### Related Components

`categorize.py`, `reference_ranges.py`.

---

## DEC-004: Switch LLM provider from Anthropic API to OpenRouter (free tier)

### Status

Accepted (Superseded an earlier setup)

### Context

Initial plan used the Anthropic API directly, with the user setting up billing/API key access. Partway through environment setup (before any pipeline code was written), the user's Anthropic API key stopped working.

### Options Considered

1. Continue troubleshooting/re-establishing Anthropic API access.
2. Switch to OpenRouter's free tier (no billing required, exposes multiple models through one API).

### Decision

Option 2 — OpenRouter free tier, accessed via the OpenAI-compatible Python SDK with a custom `base_url`.

### Reason

No credit card/billing friction; since no pipeline code had been written yet, the switch was cheap. Also introduces a genuinely useful real-world lesson (provider abstraction via a shared API shape).

### Consequences

#### Positive

- No billing setup required for the learning project.
- Exposure to a real multi-provider abstraction pattern.

#### Negative

- Free tier has real constraints: per-model shared-pool rate limiting, and a 50-requests/day account-wide cap across all free models — both were hit during the project and required real mitigation work (retry/fallback logic, and later, waiting for quota resets / a new API key).
- Vision-capable models are less abundant on the free tier than text-only models, requiring active verification (via live search) of which free models were vision-capable at any given time.

### Related Components

`pipeline.py`, `advisor.py`, `embedder.py`.

---

## DEC-005: Use Vite, not Create React App, for the frontend

### Status

Accepted

### Context

User asked to scaffold the frontend "using create-react-app."

### Options Considered

1. `create-react-app` (as originally requested).
2. Vite (modern alternative).

### Decision

Vite.

### Reason

Live search confirmed Create React App was officially deprecated by the React team on February 14, 2025, with Vite recommended as a standard modern replacement. Given the user's explicit goal of being a production-ready engineer, building new work on an actively deprecated tool was judged counter to that goal.

### Consequences

#### Positive

- Actively maintained tooling; faster dev server.

#### Negative

- None identified; this was a low-cost substitution.

### Related Components

Frontend repo scaffolding.

---

## DEC-006: Keep all exploratory/test code out of real module files — dedicated `playground.py`

### Status

Accepted (reversed an earlier informal pattern)

### Context

Early modules (`extract_report.py`, `categorize.py`, `chunker.py`) each accumulated an `if __name__ == "__main__":` block used as an ad-hoc manual test. The user flagged this as confusing for future reference, especially while still learning which parts of the code were "real."

### Options Considered

1. Continue with informal test blocks inside each module.
2. Move to proper automated tests (pytest) immediately.
3. Keep real modules clean; move all exploratory/manual testing into one dedicated scratch file (`playground.py`), explicitly not part of the real pipeline.

### Decision

Option 3.

### Reason

User's stated priorities: understanding core AI concepts is primary right now, not test infrastructure; but leaving ad-hoc test code embedded in real files creates future confusion. A dedicated scratch file solves the immediate confusion problem without requiring a testing-framework investment right now.

### Consequences

#### Positive

- Real modules stay clean and unambiguous.
- Ad-hoc experimentation remains easy and low-friction.

#### Negative

- Still no automated regression testing (tracked separately in `TODO.md`).

### Related Components

All real modules; `playground.py`.

### Related Decisions

DEC-007 (deferred automated testing).

---

## DEC-007: Defer automated testing (pytest) as a tracked but deprioritized item

### Status

Accepted

### Context

Discussion following DEC-006 about whether to introduce formal automated tests now.

### Options Considered

1. Introduce pytest now.
2. Defer it, track it explicitly as future work.

### Decision

Option 2 — deferred, tracked in the project roadmap/TODO under production-readiness concerns.

### Reason

Explicit user statement: unit tests are not the primary focus while still learning basic AI concepts; the priority is understanding, not test infrastructure.

### Consequences

#### Positive

- Keeps focus on the stated primary learning goal.

#### Negative

- Zero regression safety net for a growing codebase — accepted as a known, deliberate trade-off.

### Related Decisions

DEC-006.

---

## DEC-008: Full codebase audit and cleanup pass (dead files + stray test code)

### Status

Accepted (a one-time action, but establishes an ongoing rule)

### Context

After several ad-hoc fixes accumulated (e.g. `extract_report.py` becoming a stale duplicate once `pipeline.py` got its own improved copy of the same logic), the user asked for a full audit rather than incremental fixes.

### Decision

Performed a full file-by-file audit; deleted `hello_world.py` and `extract_report.py` (fully dead/superseded); stripped `if __name__ == "__main__":` blocks from `categorize.py`, `load_articles.py`, `chunker.py`; confirmed `build_vector_store.py` and `pipeline.py`'s own `if __name__...` blocks were legitimate entry points, not test scaffolding, and left them as-is.

### Reason

Resilience/cleanup work (like retry logic) had earlier been found inconsistently applied across files (see DEC-011); the same risk applies to dead code — a full audit catches issues a file-by-file incremental approach can miss.

### Consequences

#### Positive

- Cleaner, less confusing codebase.

#### Negative

- None identified.

### Related Components

Whole backend repo.

---

## DEC-009: Two separate GitHub repositories (backend and frontend), not a monorepo

### Status

Accepted (reversed an earlier default suggestion)

### Context

When the React frontend was first created inside the backend project folder, the default suggestion was to commit it into the same repository (a monorepo), reasoning that this was simplest for a single-developer learning project.

### Options Considered

1. Monorepo — frontend and backend in one repository.
2. Two separate repositories.

### Decision

Two separate repositories: `blood-report-analyser` (backend) and `blood-report-analyser-frontend` (frontend).

### Reason

Explicit user preference, stated directly ("No, there should be TWO separate repos"), after the monorepo approach was proposed and reasoned through. This also avoided a git "nested repository" problem, since the frontend folder had already been `git init`'d somewhat informally before the decision was finalized.

### Consequences

#### Positive

- Cleaner separation; matches how larger/real organizations often split frontend and backend ownership.

#### Negative

- Slightly more setup overhead (two repos to manage instead of one).
- Later became directly relevant to DEC-010 (the MCP server also needed to decide where to live, given this established precedent of separation).

### Related Decisions

DEC-010.

---

## DEC-010: MCP server code lives inside the backend repo, not a separate repo — but initially the opposite was chosen

### Status

Accepted (superseded an initial decision)

### Context

When planning the MCP server, the same repo-separation question from DEC-009 came up again. Initially, "brand new separate repo" was chosen (reasoning: cleaner long-term separation, consistent with the frontend precedent). This required designing the MCP server as an HTTP client of the backend's API (to avoid duplicating pipeline code across two repos). Shortly after, the user reversed this decision.

### Options Considered

1. Separate repo for the MCP server, calling the backend over HTTP (like the frontend does).
2. Same repo as the backend, with the MCP server directly importing Python pipeline functions.

### Decision

Option 2 — same repo, in a dedicated `mcp_server/` folder, directly importing `pipeline.py`.

### Reason

Explicit user reversal: "Let's build the server in the same python backend repo. No new repo for mcp server." This is simpler (no second server needed just to test locally) and reuses existing `.env` config (including the `MOCK_AI` toggle) directly.

### Consequences

#### Positive

- No code duplication; simpler local testing (no need to run two servers to test the MCP tool via HTTP).
- Reuses `MOCK_AI` mode "for free."

#### Negative

- Slight architectural inconsistency with the frontend precedent (frontend is a separate repo/HTTP client; MCP server is same-repo/direct-import) — acknowledged, not seen as a problem given the different practical constraints (frontend genuinely needs to be a separate deployable artifact; MCP server, at least for now, does not).

### Related Decisions

DEC-009.

---

## DEC-011: Apply resilience patterns (retry, fallback, timeout, defensive validation) consistently across every AI-calling file

### Status

Accepted

### Context

Retry/fallback logic was initially added only to the vision-extraction function in `pipeline.py`. A later full pipeline run crashed inside `advisor.py`, which still hardcoded a single model with no retry/fallback at all. A full audit then also found `embedder.py` had zero resilience logic, despite being called the most frequently (once per chunk during indexing, once per query during retrieval).

### Decision

Applied the same retry + multi-model-fallback pattern (a shared design, later factored into a reusable `call_model_with_fallback()` helper in `advisor.py`) consistently across `pipeline.py` (extraction), `advisor.py` (generation), and `embedder.py` (embeddings, retry-only — no fallback model existed for embeddings).

### Reason

Explicit lesson drawn from the `advisor.py` gap: "resilience patterns need to be applied consistently across every AI call in a system, not just the first one you happened to build it for."

### Consequences

#### Positive

- Much more robust pipeline against OpenRouter's real, frequently-encountered rate limits and model unavailability.

#### Negative

- No fallback model exists for embeddings specifically — a known, accepted gap (only one free embedding model was identified).

### Related Components

`pipeline.py`, `advisor.py`, `embedder.py`.

---

## DEC-012: Added a `MOCK_AI` flag for cost-free/offline development and testing

### Status

Accepted

### Context

After a real API key was arranged from a friend, the user explicitly asked to use it in "a very optimized way," avoiding testing every small change against real API calls.

### Decision

Added a `MOCK_AI` environment variable; when `true`, `pipeline.py` returns hardcoded fake data (`mock_data.py`) instead of making any real AI calls, for both extraction and advice generation.

### Reason

Enables testing the entire application's structure (uploads, API responses, MCP tool plumbing, frontend rendering) without consuming real, rate-limited API quota. Established general practice: "build a full layer, then test once" rather than testing after every micro-change.

### Consequences

#### Positive

- Essentially free, instant iteration on non-AI-logic parts of the system (routing, UI, MCP wiring).

#### Negative

- Mock-mode success does not guarantee real-mode success — real-mode confirmation is still required at meaningful checkpoints (and this gap was directly responsible for some issues, like the base64 payload problem, only surfacing once real ChatGPT testing began).

### Related Components

`pipeline.py`, `mock_data.py`, `.env`.

---

## DEC-013: Conventional Commits, one feature per commit, matching actual build order

### Status

Accepted

### Context

An initial single "Initial commit: blood report analyser project setup" commit was created, then the user asked whether the project was actually "done" given that commit message, which prompted a broader discussion about commit message accuracy.

### Decision

Restructured (and, after a formatting preference was expressed, fully redone from scratch via `rm -rf .git` + re-init, since nothing had been pushed yet) into multiple commits, one logical feature per commit, using Conventional Commits prefixes (`feat:`, `chore:`, `test:`), each with a summary line and a detailed body. Applied identically to both the backend and (later) frontend repositories.

### Reason

A single generic commit message doesn't accurately describe what's actually in a commit; explicit user preference for commit history that reads as an honest, scannable build log.

### Consequences

#### Positive

- Clean, readable, accurate git history in both repos.

#### Negative

- More upfront effort per commit (writing detailed messages) — accepted trade-off.

### Related Components

Both repositories' git history.

---

## DEC-014: MCP image input redesigned from base64 to URL-based fetch

### Status

Accepted (superseded the original tool design)

### Context

The original `analyze_blood_report(image_base64: str)` tool caused ChatGPT's client to hang indefinitely at a client-side "Encoding PNG File as Base64" step, never reaching the server at all (confirmed via server/ngrok logs showing zero incoming requests during the hang). Live research confirmed this as a known category of issue: large base64 payloads breaking MCP tool calls across multiple hosts (e.g., a documented case of Claude Code's own Drive MCP breaking above ~11KB of binary data; the test image here was 83KB).

### Options Considered

1. Shrink the image and retest (cheap experiment to confirm the size theory).
2. Use MCP's native `ImageContent` type (the theoretically "correct" protocol-level solution).
3. Return a local `file://` path from the server (suggested externally by the user, sourced from an outside snippet).
4. Redesign the tool to accept a URL; have the server fetch the image itself over HTTP.

### Decision

Option 4 — URL-based image input.

### Reason

- Option 2 was found (via research) to be currently broken specifically in ChatGPT — it doesn't render `ImageContent` properly, just dumps raw base64 as text anyway.
- Option 3 was rejected because it assumes a shared filesystem between the MCP client and server, which is false for a remote (Streamable HTTP + ngrok) deployment — ChatGPT has no access to any local file path on the user's machine.
- Option 4 sidesteps the entire large-binary-argument problem by never sending image bytes through an MCP tool argument at all; this is also a recognized real-world production pattern ("upload to storage, pass a link").

### Consequences

#### Positive

- Confirmed working via MCP Inspector.
- Scales regardless of image size/resolution.

#### Negative

- Requires the MCP server to be able to reach whatever URL it's given — currently only reliably true for URLs on the same publicly-tunneled backend host.
- Required adding a new `/upload` endpoint and static file serving to the backend, and passing images through two hops (upload → get URL → pass URL to tool) instead of one.

### Related Components

`mcp_server/server.py`, `main.py` (`/upload` endpoint, `StaticFiles` mount).

### Related Decisions

DEC-015 (merging MCP into the backend, partly driven by needing both `/upload` and `/mcp` publicly reachable simultaneously).

---

## DEC-015: Merge the MCP server into the main FastAPI backend (single process/port/tunnel)

### Status

Accepted (superseded the standalone MCP server process)

### Context

Once the backend also needed to be publicly reachable (for the `/upload`-based image URLs from DEC-014, since ChatGPT correctly refused to fetch a `127.0.0.1` URL), running two separately-tunneled services (MCP server + backend) hit ngrok's free-tier limitation: only one tunnel can be active at a time (`ERR_NGROK_334` when a second was attempted).

### Options Considered

1. Pay for ngrok / use `--pooling-enabled` to attempt multiple simultaneous free tunnels.
2. Manually toggle which service is tunneled at any given time.
3. Merge the MCP server into the same FastAPI process as the backend, so one tunnel covers both.

### Decision

Option 3 — mount the FastMCP server as an ASGI sub-application inside `main.py` at `/mcp`, with its `lifespan` wired into the parent FastAPI app.

### Reason

Simpler and more reliable than juggling tunnels or relying on free-tier pooling behavior of uncertain reliability; a single process/port/tunnel is operationally simpler regardless.

### Consequences

#### Positive

- One `uvicorn` process and one `ngrok` tunnel now cover the frontend-facing API, the upload/static-file serving, and the MCP server.
- `mcp_server/server.py` is no longer run standalone.

#### Negative

- Couples the MCP server's deployment lifecycle to the backend's — a trade-off specific to current local/testing constraints, potentially worth revisiting for a real production deployment (see `ARCHITECTURE.md` → Future Improvements).

### Related Decisions

DEC-014.

---

## DEC-016: MCP authentication set to "No Auth" (temporary), abandoning the originally-built static token approach

### Status

Accepted (temporary; explicitly flagged for revisit)

### Context

A static-token authentication mechanism (`StaticTokenVerifier` from FastMCP, with an `MCP_AUTH_TOKEN` env variable) was built and working. When connecting to ChatGPT, the connector setup UI only offered **OAuth** or **No Auth** as authentication types — no field existed for a simple static bearer token/API key, and a "Mixed" option (auto-selected after a failed OAuth handshake) did not reveal any manual token field either.

### Options Considered

1. Build full OAuth support to match what ChatGPT's UI expects.
2. Temporarily disable/remove the static token requirement and use "No Auth" for this round of testing.

### Decision

Option 2, explicitly temporary — remove the `auth=` parameter from the `FastMCP(...)` constructor for now.

### Reason

Building real OAuth was judged too large a task to block basic connectivity testing on; the ngrok URL is random/unguessable and short-lived, making "No Auth" an acceptable _temporary_ risk specifically for this local testing phase — explicitly not acceptable for any longer-lived or public exposure.

### Consequences

#### Positive

- Unblocked ChatGPT connectivity testing immediately.

#### Negative

- The MCP server currently has zero access control. Anyone who obtained the live ngrok URL while it's running could call the tool and consume the user's API quota. This is a known, explicitly flagged risk, not an oversight.

### Related Components

`mcp_server/server.py`.

---

## DEC-017: Rejected an externally-suggested "local file handler" fix for the base64/image problem

### Status

Rejected

### Context

The user pasted in an external code snippet suggesting a fix: have the server write generated images to local disk and return a `file://` path plus instructions for the client to render it via that path.

### Options Considered

See DEC-014.

### Decision

Rejected this specific suggestion.

### Reason

Two problems identified: (1) it solves the _opposite_ direction of the actual problem (image generation/output, not image upload/input); (2) it assumes a shared filesystem between client and server, which doesn't hold for a remote, ngrok-tunneled MCP server — ChatGPT cannot access any `file://` path on the user's local machine.

### Consequences

#### Positive

- Avoided implementing a fix that would not have worked for this architecture.

#### Negative

- None; correctly identified as inapplicable before implementation.

### Related Decisions

DEC-014.

---

## DEC-018: Reconcile the frontend/backend API port mismatch

### Status

Open — decision needed (found by code inspection, not yet resolved)

### Context

Reading the actual shipped code surfaced a conflict the build-history docs didn't:

- Frontend `src/components/Body.jsx` posts to `http://127.0.0.1:8005/analyze-report`.
- Backend `mcp_server/server.py` defaults `BACKEND_API_URL` to `http://127.0.0.1:8001`, and most documentation/run commands use `8001`.
  So the frontend, as written, will not reach a backend started on `8001`.

### Options Considered

1. Standardize on `8001` (matches backend default + docs); update the frontend fetch URL.
2. Standardize on `8005`; update the backend run command and `BACKEND_API_URL`.
3. Make the frontend base URL an environment variable (e.g. a Vite `VITE_API_BASE_URL`) so it isn't hardcoded at all.

### Decision

❓ NOT YET DECIDED. Recommended: Option 3 (env-driven base URL) as the durable
fix, with a single canonical default port chosen for local dev in the meantime.

### Reason

Hardcoding the base URL in a component guarantees this class of drift recurs. An
env var also eases any future real deployment (the frontend won't be talking to
`127.0.0.1`).

### Consequences

#### Positive

- Frontend and backend actually connect; no silent "upload failed" from a port typo.

#### Negative

- Minor extra config wiring if Option 3 is taken.

### Related Components

`blood-report-analyser-frontend/src/components/Body.jsx`, `main.py`,
`mcp_server/server.py`.

---

## DEC-019: Fix the missing `App.css` import in the frontend

### Status

Open — decision needed (found by code inspection)

### Context

`src/App.jsx` begins with `import "./App.css";`, but no `App.css` file exists in
the frontend repo (only `index.css` is present). Depending on the build/dev setup
this is either a hard failure or a warning, and it's a latent bug regardless.

### Options Considered

1. Remove the `import "./App.css";` line (styling currently comes from Tailwind + `index.css`).
2. Create an `App.css` file (empty or with any App-scoped styles) to satisfy the import.

### Decision

❓ NOT YET DECIDED. Either is trivial; Option 1 is simplest if no App-scoped CSS
is actually needed.

### Reason

An import of a nonexistent module is dead weight at best and a build break at
worst; it should not sit in the entry component.

### Consequences

#### Positive

- Clean build with no missing-module import.

#### Negative

- None.

### Related Components

`blood-report-analyser-frontend/src/App.jsx`.

---

## DEC-020: Reference/marker data stored in-repo as JSON (external source deferred)

### Status

Accepted

### Context

Expanding from blood-only to a general Health Report Analyzer means the
reference data (marker names, units, normal ranges, and which markers signal
which report type) will grow far beyond the original 19 blood biomarkers held
as a Python dict in `reference_ranges.py`. This raised the question of where
that data should live as it scales across many report types.

### Options Considered

1. Keep growing it as Python dicts in code.
2. Move it into structured data files (JSON) in the repo, loaded by the code.
3. Depend on an external, maintained medical data source (e.g. LOINC / a
   clinical reference-range database or API).

### Decision

Option 2 — store reference/marker data as JSON files in the repo, organized by
report type, loaded at runtime. Option 3 is acknowledged as the correct
long-term direction but deliberately deferred.

### Reason

- Treating reference data as _data, not code_ keeps it easy to grow and edit;
  adding a report type becomes "add/extend a JSON file," not "edit pipeline code."
- JSON in-repo needs no new infrastructure (the project intentionally avoids a
  DB for now), stays versioned in git, and keeps the shape stable.
- An external authoritative source is how a real "analyze any health report"
  product would eventually work (ranges are large, evolving, and vary by lab,
  method, age, and sex — a safety concern if hand-curated data goes stale). But
  adopting one now is premature for the current learning stage.
- The JSON-file approach is what makes a later swap to an external source easy:
  same data shape, different loader.

### Consequences

#### Positive

- Scales cleanly across many report types without bloating code.
- Detection (HRA-02) and categorization can both read the same JSON.
- Low friction, no new infrastructure, git-versioned.

#### Negative

- The data is hand-curated and in-repo, so it can drift from authoritative
  clinical values over time — accepted for now, revisited when moving toward
  Option 3.

### Related Components

`reference_ranges.py` (to be migrated to JSON over time), `categorize.py`,
report-type detection (HRA-02).

### Related Decisions

DEC-003 (rule-based categorization from reference data).

---

## DEC-021: Report-type detection is rule-based, from extracted marker names

### Status

Accepted

### Context

HRA-02 needed to detect which kind of report an upload is, so the pipeline can
set report_type and (later) branch per type. The question was rule-based vs.
AI-based detection, and what to detect from.

### Options Considered

1. AI classifier — send the report to a model and ask its type.
2. Rule-based — match extracted biomarker names against known "signature"
   markers per report type.
3. (Sub-question) Detect from raw report text first, vs. from the biomarker
   names already extracted by the existing pipeline.

### Decision

Rule-based detection (Option 2), matching the _already-extracted_ biomarker
names against signature markers defined in report_types.json (Option 1 of the
sub-question). Returns "unknown" when nothing matches confidently (min 2
signature hits); picks the highest-scoring type when several match.

### Reason

- Detection from known marker names is deterministic — one correct answer,
  instant and free — so plain code beats an AI call (consistent with DEC-003).
- Reuses data the pipeline already produces (extracted names); no new AI call,
  no new extraction pass.
- "unknown" is an honest result that degrades gracefully rather than guessing,
  which HRA-05 depends on.
- Detecting from extracted names (not a separate raw-text pass) is the smallest
  change that makes report_type real; the ordering can evolve when pipeline
  branching lands (HRA-09).

### Consequences

#### Positive

- Free, deterministic, testable; no AI dependency for detection.
- New report types are added as data (report_types.json), not code (DEC-020).

#### Negative

- Detection depends on extraction having produced recognizable names first.
- Multi-type ("dominant") behavior is coded but not yet demonstrable until a
  second report type's data exists.
- An AI fallback for genuinely ambiguous reports is left as possible future work.

### Related Components

`detector.py`, `report_types.json`, `pipeline.py` (analyze_report).

### Related Decisions

DEC-003 (rule-based over AI for deterministic tasks), DEC-020 (reference data
as JSON).

---

## DEC-022: HRA-04 (resilience on new AI calls) required no new code

### Status

Accepted

### Context

HRA-04 requires every new AI call added during the HRA expansion to carry
retry/fallback/timeout/defensive-validation (per DEC-011).

### Decision

Closed HRA-04 with no code change. Auditing HRA-01–HRA-03 showed they added
no new AI calls: report-type detection (HRA-02) is rule-based set intersection,
and PDF support (HRA-03) is non-AI rendering that reuses the existing,
already-resilient vision path. The three pre-existing AI calls (vision, advice,
embeddings) already carry resilience.

### Reason

HRA-04 is a standing guard, not a one-off build task. With nothing new to
protect, the correct action was to enforce the rule going forward rather than
manufacture code. Added an explicit Definition-of-Done checklist item so any
future AI call (e.g. an AI detection fallback, or the narrative extractor in
HRA-22) must include resilience before shipping.

### Related

DEC-011 (resilience on every AI call), HRA-22 (first likely future AI call).
