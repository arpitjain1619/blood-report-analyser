# Learning Journal — Blood Report Analyser (AI Engineering Fundamentals)

This document tracks everything learned hands-on while building this project — concepts, terminology, decisions, and real issues hit along the way. Updated continuously; ask to review it anytime.

---

## 🗺️ Full Roadmap (AI Engineering Concepts Covered / Remaining)

This is the master checklist — every stage of building an AI-powered product, mapped to the actual AI terminology behind it. Use this to see at a glance what's done, what's in progress, and what's left.

### Stage 0 — Environment & Tooling Foundations
- [x] **Python environment setup** — installing/verifying Python, understanding why isolated environments (`venv`/`virtualenv`) matter
- [x] **Dependency management** — installing SDKs/libraries via `pip`, understanding what a package/SDK actually is
- [x] **Secrets management** — storing API keys safely in a `.env` file instead of hardcoding them; `.gitignore` to keep secrets out of version control
- [x] **Diagnosing a restricted/corporate environment** — real-world troubleshooting skill (not AI-specific, but essential groundwork)

### Stage 1 — Talking to an LLM (the fundamentals)
- [x] **LLM API integration** — the basic request/response cycle: API key → SDK → API endpoint → model → response
- [x] **Provider abstraction** — understanding that different providers (Anthropic, OpenRouter, OpenAI) can share a similar API "shape," and how `base_url` controls who you're actually talking to
- [x] **"Hello world" call** — proving the full pipe works end-to-end before building real logic on top

### Stage 2 — Multimodal Input (Vision)
- [x] **Vision LLMs** — models that accept images (not just text) as input
- [x] **Image encoding (base64 / data URLs)** — how images are actually transmitted inside a text-based (JSON) API request
- [x] **Multimodal message structure** — sending a message with multiple content parts (text + image) instead of plain text
- [x] **Reading a real document (our blood report image)** — first real "ingestion" of user data into the system

### Stage 3 — Getting Usable Output From a Model
- [x] **Prompt engineering** — how instruction wording directly shapes model output quality/format
- [x] **Structured output (JSON mode via prompting)** — instructing a model to return machine-parseable data instead of prose
- [x] **Parsing & defensive coding** — using `json.loads()`, wrapping it in `try/except` since models don't always follow formatting instructions perfectly

### Stage 4 — Turning Raw Values Into Meaning (Categorization)
- [ ] **Direct structured lookup** — comparing extracted values against a fixed reference chart (no AI call needed) to tag High/Low/Normal
- [ ] **Design decision: rule-based logic vs. asking the AI** — understanding *when* to use plain code vs. when to delegate a task to the model (a key production judgment call)

### Stage 5 — RAG (Retrieval-Augmented Generation)
- [ ] **Knowledge base preparation** — the 14 health-guidance articles we already wrote, acting as our unstructured knowledge pile
- [ ] **Chunking** — splitting documents into smaller retrievable pieces (may be less relevant here since our articles are already short — a good real "do we even need this?" discussion)
- [ ] **Embeddings** — converting text into vectors that capture meaning, enabling semantic search
- [ ] **Vector store** — storing chunk embeddings (in-memory, to start) so they can be searched
- [ ] **Retrieval** — embedding a query (e.g. "high LDL cholesterol") and finding the most relevant article(s) via similarity search
- [ ] **Grounded generation** — feeding retrieved chunks + the categorized values into the model to generate personalized, grounded advice (not hallucinated)

### Stage 6 — Turning This Into a Real Service
- [ ] **API layer (FastAPI)** — wrapping our script logic into a real HTTP endpoint (e.g. `POST /analyze-report`) instead of a standalone script
- [ ] **Request/response design** — deciding what the client sends (an image) and what the API returns (structured categorized results + advice)
- [ ] **Basic interface** — a way to actually use the API (Swagger UI, curl, or a minimal frontend)

### Stage 7 — Production-Readiness Concepts
- [ ] **Error handling** — what happens when the model fails, returns bad JSON, or the image is unreadable
- [ ] **Proper testing (pytest)** — tracked for later; current approach uses a dedicated `playground.py` scratch file (see below) to keep real module files clean during the learning phase
- [ ] **Rate limiting awareness** — respecting/handling OpenRouter's free-tier request limits gracefully
- [ ] **Cost/token awareness** — understanding tokens in/out, even at $0 on the free tier (this matters a lot once real billing is involved)
- [ ] **Logging** — tracking what happened for debugging and auditing
- [ ] **Evaluation** — how do you actually know if the AI's output is *good*? (a real, often-skipped discipline in AI engineering)
- [ ] **Handling model unpredictability** — e.g. what we already saw with OpenRouter's free model roster rotating; designing for that kind of change
- [ ] **Safety/guardrails** — the disclaimer language baked into our knowledge base, avoiding diagnostic claims — a real requirement for any health-adjacent AI product

### Stage 8 — MCP Server (ChatGPT Integration)
- [x] **MCP fundamentals** — tools, servers, clients; giving an AI assistant "hands" to call real code
- [x] **First MCP tool** (`analyze_blood_report`) built with FastMCP, reusing existing pipeline logic directly (no duplication)
- [x] **Local testing via MCP Inspector** (stdio, then Streamable HTTP)
- [x] **Remote transport** (Streamable HTTP) for external/cloud AI hosts to connect
- [x] **Public exposure via ngrok tunnel** for testing before real deployment
- [x] **Diagnosed and fixed a large-binary-payload limitation** (base64 image argument hanging ChatGPT's client) by redesigning to a URL-fetch pattern
- [x] **Merged MCP server into the main FastAPI backend** (single process/port/tunnel) after hitting ngrok's free-tier one-tunnel-at-a-time limit
- [x] **Diagnosed and fixed stale tool-schema caching** in ChatGPT (had to fully remove/recreate the connector, not just reconnect, to force fresh schema discovery)
- [ ] Real authentication (current setup deliberately uses "No Auth" for testing only — see security note below)
- [ ] Additional tools (`explain_biomarker`, `get_reference_range`, `generate_report_pdf`) — designed conceptually, not yet built
- [ ] Real (non-ngrok) public deployment, if pursued

---

## Project Overview

**Goal:** Learn end-to-end AI product engineering by building a real project, not a toy tutorial.

**Chosen project:** Blood Report Analyser — extracts biomarkers from a blood report (image/PDF) via a vision-capable LLM, categorizes each value as High/Low/Normal against a reference chart, then generates personalized (non-diagnostic) health guidance grounded in a curated knowledge base.

**Why this project is a good learning vehicle:** It combines *two* real AI-engineering patterns in one system:
- **Direct structured lookup** (small reference chart → no search needed)
- **RAG (Retrieval-Augmented Generation)** (a pile of health-guidance articles → needs search)
Most real production AI systems use exactly this kind of hybrid, not "pure RAG for everything."

---

## Core Concepts Learned

### RAG (Retrieval-Augmented Generation)
The pattern of: (1) search your own knowledge base for relevant chunks of text, (2) hand only those chunks to the AI as context, (3) ask the AI to answer *using only* that context. Prevents the AI from making things up (**hallucinating**) about content it was never actually shown.

### Hallucination
When an AI confidently generates an answer that sounds plausible but isn't actually true/grounded — happens most often when it's asked about something outside its knowledge and it fills the gap with a guess.

### Embeddings
A way of converting text into a list of numbers (a "vector") that represents its *meaning*. Two pieces of text with similar meaning end up with similar vectors — this is what makes **semantic search** possible (finding related meaning, not just matching keywords).

### Chunking
Splitting a large document into smaller pieces (e.g. a few hundred words each) before embedding them. Needed because: (a) retrieval works better against small, focused pieces, and (b) it keeps content within the model's context limits.

### Vector store / vector database
Where chunk embeddings are stored so they can be searched later. Can be as simple as an in-memory list (what we're using, to learn the mechanics) or a dedicated tool (Chroma, Pinecone, pgvector) for production use.

### Vision LLM
An AI model that can accept and "read" images as input, not just text — needed here to read blood report images/PDFs and extract biomarker values.

### When RAG is *not* needed
Key lesson: if your knowledge is small and structured (like a lookup table of biomarker ranges), you don't need embeddings/search at all — just hand the whole thing to the model directly. RAG earns its place only when the knowledge base is too large/unstructured to include in full every time.

### SDK, base_url, and API key (from our first working call)
- **API key** — your credential to use a service.
- **SDK** (e.g. the `openai` Python package) — a code library that handles the low-level HTTP request details so you don't write raw HTTP calls yourself.
- **base_url** — tells the SDK *which company's server* to actually talk to. We used the `openai` SDK but pointed `base_url` at OpenRouter instead of OpenAI directly, since OpenRouter exposes an OpenAI-compatible API format.
- **model** — which specific AI model handles the request.

---

## Key Decisions Made

| Decision | Choice | Why |
|---|---|---|
| Backend language | Python + FastAPI | Common real-world choice for AI backends |
| Vector store | In-memory (no external DB) | See retrieval mechanics directly while learning |
| LLM provider | OpenRouter (free tier) | No billing friction; access to multiple models through one API; OpenAI-compatible format |
| Model (test call) | `openrouter/free` (auto-router) | Free lineup rotates often — auto-router avoids breakage from a specific model ID disappearing |
| Python version | Kept at 3.10.12 (did not upgrade to 3.14) | 3.10 is fully sufficient for our stack; upgrade path was blocked by locked-down environment and wasn't worth the friction for a learning project |
| Python env tooling | `pip --user` + `virtualenv` (not built-in `venv`) | System `python3-venv` package was missing and `sudo`/`apt` were blocked by IT policy on this machine |

---

## Real Issues Hit & How We Solved Them (good production-engineering experience)

1. **`sudo: cannot execute binary file`** and **`curl: cannot execute binary file`** — root cause: this is a company-managed machine with security tooling that selectively blocks specific binaries (`sudo`, `curl`) while leaving most other utilities working normally. Diagnosed by checking `file`, `mount`, `uname`, and testing which commands did/didn't work.
2. **Workaround found:** `wget` was not blocked, so we used it to bootstrap `pip` (`get-pip.py`), then used `pip install --user virtualenv` to get a working virtual environment tool without ever needing `sudo` or `curl`.
3. **Lesson:** on locked-down/corporate machines, don't assume a broken command is a bug — diagnose first (is it this one binary, or everything?), then look for an already-permitted alternate path before escalating to IT.
4. **Provider switch mid-project:** started with Anthropic's API directly, switched to OpenRouter (free tier) after the original API key stopped working. Because we hadn't written the API-calling code yet, the switch was cheap. Lesson: it's often worth deferring provider-specific code until you've confirmed the credential/account actually works.

---

## Environment Setup Summary (for reference)

```
blood-report-analyser/
├── venv/              # virtual environment (not tracked by git)
├── .env               # holds OPENROUTER_API_KEY (not tracked by git)
├── .gitignore          # ignores venv/ and .env
├── hello_world.py      # first working end-to-end API call test
```

Working "hello world" pattern (OpenRouter via OpenAI-compatible SDK):
```python
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

response = client.chat.completions.create(
    model="openrouter/free",
    messages=[{"role": "user", "content": "Say hello in one short sentence."}],
)

print(response.choices[0].message.content)
```

---

## Knowledge Base Files Created

- `blood_biomarkers_reference.md` — structured reference chart (normal ranges, high/low tiers) for direct lookup, no RAG needed
- `articles/*.md` — 14 short educational articles (one per biomarker condition), forming the RAG knowledge base for the personalized advice generation step

---

## Vision Extraction (Phase 1 of the architecture)

Confirmed working: sending an image directly to a vision-capable free model (`google/gemma-4-31b-it:free`) via OpenRouter correctly extracted real biomarker names and values from a blood report image.

### New concepts from this step

- **Vision models don't read PDFs directly** — they read images. A PDF must first be converted to image(s) per page (we initially planned this using `PyMuPDF`/`fitz`, chosen specifically because it needs no system-level tools like `poppler`, unlike some alternatives — relevant on locked-down machines). This step was skipped once we switched to testing directly with a `.png` image instead of a PDF.
- **Base64 encoding** — images can't be sent as raw binary inside a JSON API request; they must be encoded as a base64 text string first.
- **Data URL format** — `"data:image/<format>;base64,<data>"` is a standard way of embedding an image directly inside a string, used here as the value of `image_url.url`.
- **Multimodal message structure** — unlike our first "hello world" call where `content` was a plain string, image + text messages use `content` as a **list** of parts, each with its own `"type"` (`"text"` or `"image_url"`).

### Model used
`google/gemma-4-31b-it:free` — chosen because it was confirmed (via live search, Aug 2026) to be a currently free AND vision-capable model on OpenRouter.

### Result
The model correctly read and returned a full hematology panel (CBC-style values: WBC, RBC, Hemoglobin, Hematocrit, MCV, MCH, MCHC, RDW-CV, Platelets, differential counts, and absolute counts) as free-form text.

---

## Structured Output (JSON extraction)

Rewrote the prompt to explicitly demand JSON-only output (no prose, no markdown fences), then parsed the model's response with Python's built-in `json.loads()` into a real dictionary.

### New concepts from this step

- **Structured output** — instructing a model to respond in a strict, machine-parseable format (JSON here) instead of free-form prose, so code can use the result directly without manual text-scraping.
- **Prompt engineering** — the wording/instructions given to a model directly shape how usable its output is. Being explicit ("Respond with ONLY a JSON object, no other text, no markdown formatting, no code fences" + a concrete example format) is what got a clean, parseable result.
- **Defensive parsing (`try/except` around `json.loads`)** — a production habit: models don't always obey formatting instructions perfectly (smaller/free models especially), so code should anticipate malformed output rather than assume success. In our test, the model actually obeyed perfectly and parsed cleanly on the first try — but the try/except stays in the code as a safety net for cases where it doesn't.

### Result
`google/gemma-4-31b-it:free` returned valid JSON on the first attempt, correctly capturing every biomarker name/value pair from the image (CBC values, differential counts, and absolute counts) — parsed successfully into a Python dictionary, e.g. `biomarkers["Hemoglobin"]` → `15.0`.

### Milestone
This completes the full "unstructured image → structured data" pipeline: image file → base64 → vision model call → JSON string → Python dictionary. This dictionary is exactly what the next step (categorization against the reference chart) needs as input.

---

---

## Categorization (Direct Rule-Based Lookup — no AI call)

Built `reference_ranges.py` (a plain Python dict of min/max ranges) and `categorize.py` (plain comparison logic: `if value < min: "Low"`, etc.).

### Key decision made: Code vs. AI
Explicitly chose **plain Python, not an AI call**, for this step. Reasoning:
- Comparing a number against a range is **deterministic** — one correct answer every time. AI is probabilistic and can be wrong even on "obvious" comparisons — no reason to accept that risk when code is 100% reliable.
- Plain code is free, instant, and normally unit-testable, unlike AI-generated text.
- **Rule of thumb learned:** use AI for judgment/language/reasoning tasks with no single correct answer (e.g. generating advice text); use plain code for deterministic logic (e.g. numeric comparisons). Knowing *when not* to use AI is as important as knowing when to use it.

### Result
Tested against the real extracted values from the sample report — every biomarker was correctly tagged, matched against its reference range, all confirmed "Normal" for this particular report.

### Important realization for the next step
Because this sample report is entirely normal, there are **no abnormal values** to trigger the RAG/advice-generation step (our 14 knowledge-base articles are specifically written for *abnormal* conditions). We'll need either a second sample report with some abnormal values, or a manually-crafted test case, to properly test Stage 5 (RAG).

---

---

## Connecting the Pipeline (Extraction → Categorization) + Rate Limiting

### What happened
Ran `categorize.py` directly and got old/stale hardcoded test values — turned out `extract_report.py` and `categorize.py` were never actually connected; `categorize.py`'s `if __name__ == "__main__":` block only ever used its own hardcoded sample data. This is a good real lesson: **standalone test scripts are useful in isolation, but need to be explicitly wired together to form a real pipeline** — nothing connects automatically just because files are in the same folder.

### Fix: `pipeline.py`
Created a single script that:
1. Imports the reusable `categorize()` function from `categorize.py`
2. Wraps the extraction logic as a reusable `extract_biomarkers()` function
3. Chains them: image path → extraction → categorization → printed results

Confirmed working end-to-end on the synthetic abnormal report: correctly flagged Hemoglobin (Low), Total Leukocyte Count (High), Platelet Count (Low), and — interestingly — Hematocrit also came back Low even though it wasn't deliberately set abnormal, which lines up with real biology (Hematocrit and Hemoglobin are physiologically linked).

### New concept: Rate limiting & retry logic
Hit a real `429 RateLimitError` — Google's shared free-tier pool (behind `google/gemma-4-31b-it:free`) was temporarily overloaded from OpenRouter users collectively, not something wrong with our code.

- **Rate limiting** — providers cap how many requests can be made in a given time window; shared free tiers are especially prone to this since many users draw from the same pool.
- **Retry logic** — wrapped the API call in a loop with `try/except`, retrying up to a set number of times before giving up.
- **Exponential-ish backoff** — waiting progressively longer between retries (5s, 10s, 15s...) instead of retrying immediately, to avoid worsening the congestion. Standard industry pattern for any external API call, not just LLMs.
- **Fail loudly after retries exhausted** — re-`raise` the error after the last attempt rather than silently swallowing it, so failures are still visible/debuggable rather than hidden.

### Milestone
This is the first fully working, real, multi-step AI pipeline in the project: **image on disk → vision LLM → structured JSON → rule-based categorization → human-readable High/Low/Normal results**, resilient to at least one real-world failure mode (rate limiting).

---

---

## Chunking (Stage 5, Part 1)

### Deliberate learning decision
Our 14 knowledge-base articles are already short and single-topic, meaning chunking isn't strictly *necessary* here (each article could just be embedded whole). We chose to implement chunking anyway, purely for hands-on practice, so the concept is understood before encountering documents where it's actually required.

### `load_articles.py`
Reads all `.md` files from the `articles/` folder into a dict of `{filename: text}`. Confirmed all 14 articles load correctly.

### `chunker.py`
Implemented `chunk_text(text, chunk_size, overlap)` — splits text into overlapping word-count-based chunks.

### New concepts from this step
- **Chunk size** — how many words/tokens per chunk. Used a deliberately small `chunk_size=60` here just so our short articles visibly split into multiple pieces (real production chunk sizes are often 300–500 words/tokens, tuned to the embedding model and desired retrieval granularity).
- **Overlap** — chunks repeat a few words from the end of the previous chunk at the start of the next one, so sentences/ideas that fall near a chunk boundary aren't awkwardly severed with no surrounding context.
- **When chunking is/isn't needed** — chunking solves two specific problems: (1) documents too large to fit in context, and (2) documents covering multiple topics where splitting helps retrieval target the *relevant* part. Neither applies to our short, single-topic articles — but implemented anyway for learning purposes.

### Result
Confirmed visually: `anemia_low_hemoglobin.md` (~200 words) split into 4 overlapping chunks, with visible repeated text between consecutive chunks confirming the overlap mechanic works as intended.

---

---

## Code Organization Decision: Keeping Real Modules Clean

### The problem noticed
Early modules (`extract_report.py`, `categorize.py`, `chunker.py`) each had an `if __name__ == "__main__":` block used as an ad-hoc manual test. This works during development, but leaving it in permanently clutters the real code and is confusing for future reference — especially while still learning which parts are "real" vs. exploratory.

### The fix
- Real module files (`embedder.py`, and going forward) now stay **clean** — just the reusable function(s), no embedded test/demo code.
- All exploration/testing happens in a separate, explicitly-scratch file: **`playground.py`** — clearly not part of the real pipeline, safe to overwrite or delete anytime, used purely to poke at new concepts as they're introduced.
- This mirrors a real engineering practice: keeping a throwaway scratch file separate from production code, so "what's real" is never ambiguous.
- Proper automated testing (`pytest`) remains a tracked item for later (Stage 7), once the pipeline stabilizes — not a priority while still learning core concepts.

---

---

## Embeddings & Vector Store (Stage 5, Parts 2–3)

### Conceptual explanation given (recap for reference)
- **Embedding** = the "coordinates" of a piece of text on an invisible, high-dimensional "map of meaning." Text with similar meaning ends up with similar coordinates (numbers close together); unrelated text ends up far apart. Our embedding model represents any input (short or long) as exactly **2048 numbers** — no single number means anything alone; meaning lives in the overall pattern across all 2048 together.
- **Vector store** = simply the storage/filing system holding `{original text, its coordinates}` pairs for every chunk, so they can be searched later. Ours is intentionally simple: a JSON file, not a dedicated vector database — the concept is identical either way, just a difference in storage sophistication.
- **Why this enables search**: once everything has coordinates, finding "the most relevant article" becomes a math problem — find the saved chunk whose coordinates are *closest* to the query's coordinates (via **cosine similarity**, to be implemented in the retrieval step next) — not keyword/string matching.

### `embedder.py`
Wraps `client.embeddings.create()` using the free `nvidia/llama-nemotron-embed-vl-1b-v2:free` model via OpenRouter (same client/base_url as chat calls, different method).

**Bug hit & fixed:** SDK defaulted to `encoding_format="base64"`, which this NVIDIA model doesn't support — fixed by explicitly passing `encoding_format="float"`.

### `build_vector_store.py`
One-time "build/index" script (intentionally kept as a direct-run script, not a reusable module — different from our "keep modules clean" rule since this genuinely *is* a standalone build step): loads all articles → chunks each → embeds each chunk → saves `{article, chunk_index, text, embedding}` for every chunk into `vector_store.json`. Included a small `time.sleep(1)` between calls to stay under free-tier rate limits.

### Bug hit & fixed: stale/inactive virtual environment
Got `ModuleNotFoundError: No module named 'dotenv'` despite it being installed earlier — root cause was simply that the venv wasn't active in that terminal session (`which python3` pointed to system Python, not the project's `venv`). Reactivating with `source venv/bin/activate` fixed it immediately. **Lesson:** venv activation is per-terminal-session, not persistent — easy to forget after opening a new terminal or restarting.

### Result
Successfully embedded and saved **47 chunks** (from 14 articles) into `vector_store.json` — our actual, persistent vector store now exists on disk.

---

---

## Retrieval (Stage 5, Part 4) — Semantic Search Working

### `retriever.py`
- `cosine_similarity(vec_a, vec_b)` — measures the *angle* between two vectors using `numpy` (`np.dot` / `np.linalg.norm`); closer to `1.0` = more similar meaning, closer to `0` = unrelated.
- `retrieve_relevant_chunks(query, vector_store, top_k)` — embeds the incoming query text, compares it against every stored chunk's embedding via cosine similarity, sorts by score, returns the top matches.

### Test & result
Queried `"Hemoglobin is Low"` against the 47-chunk vector store. Correctly retrieved both chunks from `anemia_low_hemoglobin.md` as the top 2 matches (scores 0.6489 and 0.5262) — found purely through embedding/coordinate math, with **zero keyword-matching rules written**. This is the core proof of semantic search: the system matched on *meaning* ("Hemoglobin is Low" ≈ "Low Hemoglobin / Anemia"), not shared exact words alone.

### Milestone
Full RAG retrieval loop now confirmed working end-to-end: text query → embed → compare against stored chunk embeddings → return most relevant chunk(s). This is "Machine A" (retrieval) from our very first RAG explanation, now real and tested.

---

---

## Full Codebase Cleanup Pass

Did a complete audit of every file for dead code and stray test blocks, rather than fixing files one at a time as they happened to come up.

**Deleted (fully dead/superseded):**
- `hello_world.py` — one-off demo script, superseded by `pipeline.py`
- `extract_report.py` — old duplicate extraction logic, no longer imported anywhere once `pipeline.py` got its own (improved, fallback-enabled) version

**Stripped `if __name__ == "__main__":` test blocks from:**
- `categorize.py`
- `load_articles.py`
- `chunker.py`

**Confirmed correctly structured, left as-is:**
- `build_vector_store.py` and `pipeline.py` both have `if __name__ == "__main__":` blocks — but these are legitimate direct-run entry points (a build step and the real application respectively), not leftover test scaffolding, so they're correctly following the "modules stay clean, entry points can run directly" rule established earlier.

**Lesson reinforced:** resilience/cleanup passes need to be applied consistently across an entire codebase, not just the file currently being worked on — same lesson as the earlier retry-logic gap in `advisor.py`.

---

---

## Hit the Daily Free-Tier Quota (Account-Level, Not Per-Model)

### What happened
After many pipeline runs during testing, hit a `429` with `limit_source: openrouter_free_tier_daily` — OpenRouter's free tier caps requests at **50/day per account**, shared across *all* free models combined (not per-model). Our earlier fallback logic (switching between 3 vision models) didn't help here, because all three draw from the same account-wide daily bucket.

### Key lesson
**Model fallback and account-quota limits are two different failure modes.** Fallback logic solves "this specific model/provider is temporarily congested." It does nothing against "my account has used its total daily allowance" — that requires either waiting for the reset window or increasing the quota (OpenRouter: purchasing $10 credit raises the cap from 50/day to 1,000/day).

### Better dev practice identified (to implement next)
Repeated full pipeline runs during debugging were burning real quota on the *vision extraction* step even when only testing *downstream* logic (categorization, retrieval, advice generation). Going forward: **cache extraction results locally** so iterative testing of downstream steps doesn't require repeated (rate-limited) API calls. General principle: avoid needlessly re-calling expensive/rate-limited external APIs during iterative development.

---

---

## Version Control & GitHub (Stage 6 prep)

### Setup
Initialized git (`git init`), configured `.gitignore` to exclude `venv/`, `.env`, `__pycache__/`, `*.pyc`, and `vector_store.json` (a regenerable build artifact, deliberately not committed).

### Key safety step
Before staging anything, ran `git status` first to manually review every file git saw — specifically to confirm `.env` (real API key) wasn't about to be tracked, and that no real personal blood report data remained in the folder (confirmed clean — only the synthetic mock report exists). This check-before-commit habit matters especially for a public repo.

### Commit strategy
Restructured into **11 separate, feature-scoped commits** (rather than one large "initial commit"), each using **Conventional Commits** formatting (`feat:`, `test:`, `chore:` prefixes) with a summary line + detailed body. Commits follow the actual build order: gitignore → categorization → knowledge base → chunking/loading → embeddings → vector store builder → retrieval → advice generation → full pipeline → sample test data → scratch playground file.

**New concept: Conventional Commits** — a standardized commit message format (`type: short summary`, optionally with a longer body) that makes project history scannable and machine-parseable (many tools auto-generate changelogs from this format). Common types include `feat` (new feature), `fix` (bug fix), `chore` (tooling/config), `test` (test-related).

**Lesson:** git history doesn't have to be built "live" as you go — since nothing had been pushed yet, we safely wiped and rebuilt history (`rm -rf .git` + re-init) once we decided on a better commit structure. Once something is pushed/shared, rewriting history becomes much riskier — this was a good moment to get it right, right before pushing.

### Result
Repository created as **public** on GitHub, with a concise (<350 char) description honestly reflecting current scope, including that it's currently a CLI pipeline, not yet an API/service. Pushed successfully — all 11 commits now live and visible.

---

---

## Stage 6 — FastAPI Backend (Part 1: Endpoint + Mock Mode)

### Refactor: pipeline.py as a reusable function
Extracted the full pipeline logic out of the `if __name__ == "__main__":` block into a proper reusable function, `analyze_report(image_path) -> dict`. This is what lets the *same* pipeline logic be called from both the CLI entry point and, now, a FastAPI endpoint — a script and a reusable module need to be structured differently, and this is why.

### New concept: Mock mode for cost-free/offline development
Added a `MOCK_AI` flag (read from `.env`) that swaps real AI calls for hardcoded fake data (`mock_data.py`) when enabled. This is a real, common industry practice: developers shouldn't need to hit live, rate-limited, or costly external APIs just to test that application *plumbing* (uploads, routing, response shape) works correctly. Real AI calls are reserved for deliberate, meaningful test passes — not every small change.

### New concept: Budget-conscious API usage strategy
Given a freshly-arranged real API key, explicitly adopted a "build a full layer, then test once" workflow instead of testing after every small change — batching verification into meaningful checkpoints (e.g. "confirm the whole FastAPI layer works in mock mode" as one checkpoint, "confirm it works with real AI" as a separate, later checkpoint) rather than spending quota on every micro-step.

### `main.py` — the FastAPI application
- **`FastAPI()`** — the web framework instance
- **Routes** (`@app.get("/")`, `@app.post("/analyze-report")`) — decorators mapping an HTTP method + URL to a Python function; this is the core mechanic of any web API
- **`UploadFile = File(...)`** — FastAPI's mechanism for accepting file uploads over HTTP
- **Temp file handling** — uploaded bytes are saved to a temporary file on disk (`tempfile.NamedTemporaryFile`) since the existing `analyze_report()` function expects a file path, not raw bytes; cleaned up afterward in a `finally` block regardless of success/failure
- **CORS (`CORSMiddleware`)** — a browser security feature that blocks a webpage on one origin (domain/port) from calling an API on a different origin unless explicitly allowed. Required once the React frontend (running on its own port) needs to call this API.
- **Error handling** — real exceptions from the AI pipeline are caught and returned as proper HTTP 500 errors with a message, instead of crashing the server silently

### Running the server
`uvicorn main:app --reload` — `uvicorn` is the actual server process that listens for HTTP requests; FastAPI just defines what happens when one arrives. `--reload` auto-restarts on code changes during development.

**Issue hit:** "Address already in use" on port 8000 — a previous server process hadn't fully stopped. Resolved by running on an alternate port (`--port 8001`) rather than hunting down and killing the stale process.

### Result
Full test via `curl -X POST .../analyze-report -F "file=@sample_report.png"` in `MOCK_AI=true` mode returned a correctly structured JSON response (`biomarkers`, `categorized`, `advice`) — confirming the entire upload → temp file → pipeline → JSON response chain works correctly, at zero cost, before spending any real API quota.

---

---

## Stage 6 — Real End-to-End API Test (Success) + Bugs Fixed Along the Way

### Bugs hit and fixed before the successful run
1. **Crash on malformed model response** — `'NoneType' object is not subscriptable` when a model returned an empty/unexpected response shape. Fixed with an explicit defensive check (`if not response.choices or not response.choices[0].message.content: raise ValueError(...)`) before attempting to parse — converts a confusing crash into a clean, already-handled error.
2. **No request timeout** — a hung request could stall indefinitely. Added `timeout=30` to the API call.
3. **`uvicorn --reload` restarting mid-request** — the dev auto-reload feature detected a file change during a long-running request (likely from temp-file activity) and restarted the whole server, silently discarding all progress through the fallback chain and restarting from the first model. Fixed by running without `--reload` for real-mode testing.
4. **Reduced retries-per-model from 2 to 1** — since failures were mostly shared-pool congestion (not transient), retrying the same model rarely helped; moving faster to the next fallback model was a better use of limited time/quota.
5. **Post-restart venv deactivation (recurring theme)** — after a full system restart, `uvicorn: command not found` — same root cause as the earlier `dotenv` issue: a fresh terminal has no venv active by default. Reinforces: venv activation is per-session, always worth checking with `which python3` when something "used to work."

### Result: full real end-to-end success
`POST /analyze-report` with a real image returned `200 OK` with genuine (non-mock) results:
- Correct vision extraction and categorization (matching prior known-good values)
- **Grounded RAG advice**, correctly explaining Hemoglobin/Hematocrit together as anemia-related, flagging the high WBC count, and — notably — giving only generic guidance for low platelets rather than inventing specific advice, because no knowledge-base article exists for that biomarker. This is RAG grounding working as intended: the model didn't hallucinate detail it was never given.

### Milestone
The full AI pipeline (vision extraction → categorization → RAG retrieval → grounded generation) is now a real, working HTTP API, callable by any client — not just a local script.

---

---

## Stage 8 (New) — MCP Server: First Tool (`analyze_blood_report`)

### New concept: MCP (Model Context Protocol)
A standardized way for an AI assistant (ChatGPT, Claude, etc.) to call real code/tools, not just generate text. An MCP **server** exposes one or more **tools** — each with a name, description, and typed inputs/outputs — that an MCP **client** (the AI host application) can discover and call. The AI reads the tool's description (often the function's docstring) to decide *when* and *how* to call it, then receives the real result to use in its response — the AI equivalent of "giving the assistant hands," not just a voice.

### Architecture decision: MCP server as a thin translator, not duplicated logic
Rather than reimplementing pipeline logic in a separate service/repo, the MCP server lives **inside the existing backend repo** (`mcp_server/server.py`) and directly imports and calls the already-proven `analyze_report()` function from `pipeline.py`. This mirrors the "one backend, multiple clients" pattern: the React frontend and the MCP server are both just different *clients* of the same underlying logic — no duplication, no drift risk between two copies of the same code.

### Library choice: FastMCP
Confirmed (via live search) as the current standard, decorator-based framework for building MCP servers in Python — used by ~70% of MCP servers in the wild. A plain Python function becomes an AI-callable tool just by adding `@mcp.tool` above it; FastMCP auto-generates the tool's schema from type hints and turns the docstring into the tool's AI-facing description.

### New concept: cross-folder imports via `sys.path`
Since `server.py` lives in a subfolder (`mcp_server/`) but needs to import `pipeline.py` from the project root, added `sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))` — explicitly tells Python to also look one directory up when resolving imports. This is how Python resolves cross-folder imports without a formal installable package structure.

### `mcp_server/server.py` — the `analyze_blood_report` tool
- Accepts `image_base64: str` (MCP tools take structured arguments, not raw file uploads — unlike our FastAPI endpoint)
- Decodes the base64 string back into real image bytes, writes to a temp file, calls `analyze_report()` (unchanged), cleans up the temp file afterward
- **The docstring is a safety-relevant design choice, not just documentation** — it explicitly tells any AI host that results are "not a medical diagnosis," shaping how the tool gets described/used by the calling AI itself, not just the generated advice text

### Testing: MCP Inspector
Standard local tool for testing an MCP server without needing a full AI host (ChatGPT/Claude) connected yet: `npx @modelcontextprotocol/inspector python3 mcp_server/server.py`. Opens a local web UI showing available tools and letting you manually trigger calls with real arguments — this is how the very first test was run.

### Result
First test, in `MOCK_AI=true` mode (zero cost): the Inspector successfully called `analyze_blood_report` with a base64-encoded test image, and got back the full expected JSON shape (`biomarkers`, `categorized`, `advice`) — confirming the entire MCP wiring (base64 decode → temp file → existing pipeline → structured tool result) works correctly, before any real AI-provider cost was spent.

### Bug hit & fixed (recurring theme)
`ModuleNotFoundError: No module named 'openai'` when first running `server.py` — same root cause as twice before: venv not active in the current terminal session. Reinforces: **always check `which python3` first** when something "should just work" and doesn't.

---

---

## MCP Image-Input Redesign: Base64 → URL-Based Fetch

### Problem discovered
`analyze_blood_report(image_base64: str)` hung indefinitely in ChatGPT at a client-side "Encoding PNG File as Base64" step — never even reached our server (confirmed via server/ngrok logs showing zero new requests during the hang). Verified via research this is a known, documented category of issue: large base64 payloads breaking MCP tool calls across multiple hosts (a real example found: Claude Code's own Drive MCP breaking above ~11KB of binary data). Our test image was 83KB — comfortably over that kind of threshold.

### Why MCP's "proper" image type doesn't help either
MCP has a native `ImageContent` type for binary data, which in theory is the "correct" way to send images. Research surfaced a specific report ("MCP Has an Image Problem") showing ChatGPT doesn't render `ImageContent` correctly yet — it just dumps raw base64 as text. So even the spec-correct approach is currently broken on ChatGPT specifically.

### Rejected alternative: local file path (`file://...`)
A suggested fix returning a `file://` path assumes the MCP client and server share a filesystem — true only for local/stdio setups (e.g. Claude Desktop launching a local server). Doesn't apply to us: we deliberately run remote (Streamable HTTP + ngrok) specifically so a cloud-hosted AI can reach us at all, so ChatGPT has no access to any path on the local machine.

### The fix: URL-based input instead of embedded bytes
Redesigned the flow so binary data never travels through an MCP tool argument at all:
1. **New `/upload` endpoint on the FastAPI backend** (`main.py`) — accepts a file, saves it to a local `uploads/` folder (served via `StaticFiles`), returns a relative URL (e.g. `/uploads/<uuid>.png`)
2. **`analyze_blood_report` tool signature changed**: `image_base64: str` → `image_url: str`. The tool now fetches the image itself via `httpx.get(...)`, using `BACKEND_API_URL` (from `.env`) to resolve relative paths
3. Since only **our own MCP server** (not ChatGPT) needs to reach that URL to fetch the bytes, `localhost` URLs work fine here — ChatGPT only ever handles a short string, never the image itself

This mirrors a common real-world production pattern: "upload to storage, pass a link" — not a hack specific to this project.

### Bug hit & fixed along the way
`FileNotFoundError` on `/upload` — the `uploads/` folder existed at server startup but was later deleted (likely via cleanup/gitignore-related actions) and never recreated. Fixed by calling `os.makedirs("uploads", exist_ok=True)` defensively inside the endpoint itself, not just once at startup — a small but real lesson: directories a running server depends on can disappear during its lifetime; critical paths should be self-healing, not assumed permanent.

### Result
Confirmed working end-to-end via MCP Inspector using the new `image_url` parameter — real fetch-and-analyze succeeded.

---

## Merging the MCP Server into the Backend (ngrok Free-Tier Constraint)

### Problem discovered
Once the backend also needed a `/upload` endpoint (for the URL-based image fix above) and needed to be *publicly* reachable too (ChatGPT correctly refused to fetch a `127.0.0.1` URL — a real, sensible client-side safety check, not a bug), running two separate tunneled services (MCP server on one port/tunnel, backend on another) hit a wall: **ngrok's free tier only allows one active tunnel at a time.** Attempting a second tunnel returned `ERR_NGROK_334`.

### The fix: one process, one port, one tunnel
Rather than fight the tunnel limit (e.g. paying for ngrok, or juggling which service is tunneled at a given moment), merged the MCP server *into* the FastAPI backend as a mounted sub-application:

```python
mcp_app = mcp_server_instance.http_app(path="/")
app = FastAPI(title="...", lifespan=mcp_app.lifespan)
app.mount("/mcp", mcp_app)
```

**New concept: ASGI sub-application mounting** — a FastMCP server is itself a small ASGI app; FastAPI supports mounting one app inside another at a URL prefix (`/mcp`), so multiple logical services can share a single physical server process. `mcp_server/server.py` is no longer run standalone (`python3 mcp_server/server.py` is retired) — it's now purely imported code, wired into `main.py`'s single `uvicorn` process.

**Gotcha:** FastMCP's session handling requires its `lifespan` (startup/shutdown hook) to be passed into the *parent* FastAPI app at creation time (`FastAPI(lifespan=mcp_app.lifespan)`) — easy to miss, causes obscure startup issues if skipped.

### Result
One `uvicorn main:app --port 8001` process now serves the React-facing API, the `/upload` endpoint, static file serving (`/uploads/...`), **and** the MCP server (`/mcp`) — all reachable through a single ngrok tunnel (`ngrok http 8001`). Simpler operationally (2 terminal tabs instead of 3-4) and sidesteps the free-tier tunnel limit entirely.

---

## Stale MCP Tool Schema Caching in ChatGPT

### Problem discovered
After redesigning the tool from `image_base64` to `image_url` and restarting the server with the new code, ChatGPT continued sending the *old* argument (`image_base64`), causing the server to correctly reject the call (`missing_argument: image_url`, `unexpected_keyword_argument: image_base64` — visible in server logs). The server was verified to be running the new code; the mismatch was entirely on ChatGPT's side.

### Root cause
MCP clients typically discover a tool's schema (its parameters) once, at connection time, and don't necessarily re-fetch it just because the underlying server changed. Toggling the connector off/on was **not** sufficient to force a refresh.

### Fix
Fully **removed and recreated** the connector in ChatGPT (Plugin Management → Remove, then re-add as a brand new plugin with the same URL) — this forces a genuinely fresh discovery handshake, rather than reusing a cached session/schema. Also started a **new conversation** afterward, since an existing chat thread may itself have cached tool definitions mid-conversation.

### Lesson
When an AI client's behavior doesn't match a server's current, verified-correct code, the mismatch may be **client-side caching**, not a server bug — worth checking server logs directly (as done here) to see the *actual* arguments being sent, rather than assuming the server is at fault.

### Test prompts prepared for validation (not all yet run)
1. Explicit tool invocation with a real image URL (control test)
2. Schema-only question ("What parameters does the analyze_blood_report tool expect?") — fastest way to confirm the schema refreshed, without a full pipeline run
3. Natural language without explicitly naming the tool — tests whether ChatGPT chooses to use it on its own
4. Deliberately invalid URL — tests error handling/surfacing
5. Follow-up question about a result — tests whether ChatGPT treats the tool's actual output as ground truth or drifts into its own general knowledge

---

## Status / Where We Are

✅ Environment set up (Python, venv, dependencies)
✅ API key working (OpenRouter)
✅ Vision extraction, structured JSON output, and categorization all confirmed working on real data
✅ Full RAG pipeline (chunking, embeddings, vector store, retrieval, grounded generation) confirmed working end-to-end for real
✅ Retry/backoff, multi-model fallback, defensive response handling, and request timeouts for resilience
✅ Full codebase cleanup; project pushed to public GitHub repo with clean conventional-commit history; README added
✅ FastAPI backend built with `/analyze-report` endpoint, CORS, file upload handling, mock mode for cost-free dev/testing
✅ **Full real end-to-end API test successful** — real image in, grounded advice out, via HTTP
✅ **MCP server built, exposed remotely, and connected to ChatGPT** — tool discovery confirmed working; image-input redesigned from base64 (broken) to URL-based fetch; merged into the main backend to work within ngrok's free-tier single-tunnel limit; resolved a stale-schema-caching issue by fully recreating the ChatGPT connector
🔜 Next: confirm the URL-based tool call succeeds end-to-end in ChatGPT with the refreshed schema (test prompts prepared); then design/build additional MCP tools (`explain_biomarker`, `get_reference_range`, `generate_report_pdf`); separately: enhance the 14 knowledge-base articles and restructure advice generation to be per-biomarker structured output (requested, not yet started)

*(This section will be updated as we progress through additional MCP tools, article/advice enhancements, PDF export, real authentication, and remaining production concerns.)*
