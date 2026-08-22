# Blood Report Analyser

An **AI-powered blood report analysis pipeline**, built with Python and
FastAPI. Upload a photo of a blood test report, and the system uses a
**vision-language model (VLM)** to extract biomarker values, a deterministic
rules engine to flag abnormal ones, and **Retrieval-Augmented Generation
(RAG)** to produce grounded, personalized, non-diagnostic health guidance.

Built as a hands-on learning project to explore real-world **AI engineering**
end to end: multimodal LLM inference, structured output extraction,
embeddings, semantic search, RAG, and production-minded concerns like
rate-limit resilience, multi-model fallback, and mock-mode testing.

> ⚠️ **Educational project only.** Not a medical device, and not a substitute
> for professional medical advice. All generated guidance is general and
> non-diagnostic, and always recommends consulting a licensed doctor.

> This repo used to also contain a React frontend; it has since been split
> out into its own separate project. This README now covers the Python/AI
> backend exclusively.

## Contents

- [What It Does](#what-it-does)
- [Architecture](#architecture)
- [AI / ML Concepts Demonstrated](#ai--ml-concepts-demonstrated)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Running the API](#running-the-api)
- [Pipeline Walkthrough](#pipeline-walkthrough)
- [Stage 1 — Vision Extraction](#stage-1--vision-extraction)
- [Stage 2 — Categorization](#stage-2--categorization)
- [Stage 3 & 4 — RAG: Retrieval and Grounded Generation](#stage-3--4--rag-retrieval-and-grounded-generation)
- [Resilience: Retries & Multi-Model Fallback](#resilience-retries--multi-model-fallback)
- [Mock Mode](#mock-mode)
- [API Reference](#api-reference)
- [MCP Server & ChatGPT Integration](#mcp-server--chatgpt-integration)
- [File-by-File Reference](#file-by-file-reference)
- [Extending the Knowledge Base](#extending-the-knowledge-base)
- [Roadmap](#roadmap)
- [Disclaimer](#disclaimer)

## What It Does

1. A client uploads an image of a blood test report to the API.
2. The FastAPI backend runs it through an AI pipeline:
   - A **vision-language model (VLM)** reads the image and extracts
     biomarker name/value pairs as structured JSON — no OCR library, no
     manual parsing, just a multimodal LLM call with a tightly constrained
     prompt.
   - Each value is **categorized** (High / Low / Normal) against a
     reference-range table — a deterministic, non-AI step, deliberately kept
     rule-based rather than delegated to the model.
   - For every abnormal biomarker, the system performs **semantic
     retrieval**: it embeds a query, searches a **vector store** of
     biomarker-guidance articles by **cosine similarity**, and pulls back
     the most relevant chunks (**RAG retrieval**).
   - An LLM then **generates** personalized guidance, explicitly instructed
     to use *only* the retrieved context — a **grounding** strategy that
     reduces hallucination risk — and to always end with a doctor-consult
     disclaimer.
3. The API returns the categorized biomarkers and the generated advice as
   JSON.

## Architecture

One request, traced top to bottom — image in at the top, advice back out at
the bottom:

```
┌──────────────────────────────────────────────────┐
│                    API Client                     │
│         (any HTTP client, e.g. a frontend)        │
└──────────────────────────────────────────────────┘
                          │
                          │  1. upload report image
                          │     POST /analyze-report (multipart/form-data)
                          ▼
┌──────────────────────────────────────────────────┐
│                 FastAPI Backend                  │
│                    (main.py)                     │
└──────────────────────────────────────────────────┘
                          │
                          │  2. pipeline.analyze_report(image)
                          ▼
┌──────────────────────────────────────────────────┐
│           Stage 1 · Vision Extraction            │
│        VLM reads image -> biomarker JSON         │
│       OpenRouter vision models + fallback        │
└──────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────┐
│             Stage 2 · Categorization             │
│          rule-based High / Low / Normal          │
│             vs. reference_ranges.py              │
└──────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────┐
│             Stage 3 · RAG Retrieval              │
│     embed query -> cosine similarity search      │
│     over vector_store.json (article chunks)      │
└──────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────┐
│          Stage 4 · Grounded Generation           │
│       LLM writes advice from top-k chunks        │
│        OpenRouter text models + fallback         │
└──────────────────────────────────────────────────┘
                          │
                          │  3. returns {biomarkers, categorized, advice}
                          ▼
┌──────────────────────────────────────────────────┐
│                 FastAPI Backend                  │
└──────────────────────────────────────────────────┘
                          │
                          │  4. JSON response
                          ▼
┌──────────────────────────────────────────────────┐
│                    API Client                     │
└──────────────────────────────────────────────────┘
```

Stages 1 and 4 are the two points where the pipeline calls out to an LLM on
OpenRouter (with model fallback); stage 3 is a local, non-network semantic
search over `vector_store.json`; stage 2 is plain deterministic Python, no
model call at all.

## AI / ML Concepts Demonstrated

This project is intentionally built to touch a broad slice of practical AI
engineering, rather than depending on a single high-level framework:

- **Multimodal LLM inference** — a vision-language model (VLM) reads an
  image directly (base64-encoded, inlined in the prompt) rather than going
  through a separate OCR pipeline.
- **Structured output extraction** — the model is prompted to return *only*
  strict JSON, which is then parsed directly. No function-calling API is
  used; structure is enforced entirely through prompt design.
- **Prompt engineering** — tightly scoped instructions (exact format
  examples, explicit constraints like "no markdown formatting") to get
  reliable, parseable output from free-tier models.
- **Embeddings** — text is converted into dense vector representations via
  an embedding model, both for the knowledge-base articles (offline, at
  index-build time) and for runtime queries.
- **Vector store & semantic search** — a lightweight, from-scratch vector
  store (a JSON file of `{text, embedding}` pairs) queried via manual
  **cosine similarity**, deliberately avoiding a managed vector database to
  make the retrieval mechanics fully transparent.
- **Chunking** — knowledge-base articles are split into overlapping,
  fixed-size word chunks so retrieval can surface a focused passage instead
  of an entire article.
- **Retrieval-Augmented Generation (RAG)** — retrieved chunks are injected
  into the generation prompt as context, so the model's output is grounded
  in a curated knowledge base instead of relying purely on parametric
  (pretrained) knowledge.
- **Grounding & hallucination mitigation** — the generation prompt
  explicitly restricts the model to *only* the retrieved context and
  forbids diagnosis or medication recommendations.
- **Model fallback & resilience** — both the vision and text generation
  steps iterate through a list of models with retries and backoff, so a
  rate-limited or unavailable free-tier model doesn't take down the whole
  pipeline.
- **Mock mode** — an `MOCK_AI` environment flag swaps in canned
  biomarkers/advice, letting the API and app plumbing be tested end-to-end
  without burning LLM quota or waiting on network calls.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI, Uvicorn |
| LLM provider | [OpenRouter](https://openrouter.ai) (free-tier models), via the OpenAI-compatible SDK |
| Vision-language model | `google/gemma-4-31b-it:free` (+ fallback models) |
| Embedding model | `nvidia/llama-nemotron-embed-vl-1b-v2:free` |
| Vector store | Local JSON file (`vector_store.json`) — no external vector DB |
| MCP server | [FastMCP](https://github.com/jlowin/fastmcp), mounted into the FastAPI app; exposes an `analyze_blood_report` tool to MCP-compatible clients (e.g. ChatGPT) |
| Tunneling (dev) | [ngrok](https://ngrok.com) — exposes the local API/MCP server over a public HTTPS URL for remote clients |

## Project Structure

```
blood-report-analyser/
├── main.py                 # FastAPI app: /analyze-report, /upload, mounts MCP at /mcp
├── mcp_server/
│   └── server.py            # FastMCP server: analyze_blood_report tool
├── pipeline.py              # Orchestrates the full pipeline (image → advice)
├── categorize.py            # Rule-based High/Low/Normal categorization
├── reference_ranges.py      # Biomarker normal-range reference chart
├── load_articles.py         # Loads knowledge-base articles from disk
├── chunker.py                # Splits article text into overlapping chunks
├── embedder.py                # Text → embedding vector, via OpenRouter
├── build_vector_store.py      # One-time script: chunk + embed all articles
├── retriever.py                # Semantic search via cosine similarity
├── advisor.py                   # Generates grounded advice using RAG
├── mock_data.py                  # Canned biomarkers/advice for MOCK_AI mode
├── articles/                      # RAG knowledge base (biomarker guidance)
├── uploads/                        # Images uploaded via /upload (gitignored)
├── vector_store.json              # Generated embeddings (gitignored)
├── sample_report.png              # Synthetic sample report for testing
└── playground.py                   # Scratch file for exploring concepts
```

## Setup

```bash
python3 -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate

pip install fastapi uvicorn openai python-dotenv numpy pillow fastmcp httpx
```

Create a `.env` file in the repo root:

```bash
OPENROUTER_API_KEY=your-openrouter-key-here
MOCK_AI=false
BACKEND_API_URL=http://127.0.0.1:8001
```

- `OPENROUTER_API_KEY` — API key for [OpenRouter](https://openrouter.ai),
  which proxies requests to various free-tier LLMs using an
  OpenAI-compatible API. Every model call in this project (vision
  extraction, embeddings, advice generation) goes through the same
  `OpenAI` client, just pointed at OpenRouter's `base_url`.
- `MOCK_AI` — when `true`, skips all real model calls and returns canned
  data. See [Mock Mode](#mock-mode).
- `BACKEND_API_URL` — base URL the MCP server resolves relative
  `/uploads/...` image paths against (see
  [MCP Server & ChatGPT Integration](#mcp-server--chatgpt-integration)).
  Defaults to `http://127.0.0.1:8001`.

Before running the pipeline for the first time, build the RAG vector store
(one-time — only needs re-running if you edit/add articles):

```bash
python3 build_vector_store.py
```

This reads every article in `articles/`, chunks it, embeds each chunk, and
writes the result to `vector_store.json` (gitignored — regenerate locally).

## Running the API

```bash
uvicorn main:app --reload --port 8001
```

This single process serves the REST API (`/analyze-report`, `/upload`),
the uploaded-image static files (`/uploads/...`), and the MCP server
(`/mcp`) — see [MCP Server & ChatGPT Integration](#mcp-server--chatgpt-integration)
for wiring this up to a remote client like ChatGPT.

You can also run the pipeline directly from the command line without the API
layer at all:

```bash
python3 pipeline.py
```

This runs `analyze_report()` against `sample_report.png` and prints the
categorized biomarkers and generated advice to stdout — useful for quickly
testing pipeline changes without spinning up the server.

> Want to test the app without making real LLM calls? Set `MOCK_AI=true` in
> `.env` — see [Mock Mode](#mock-mode) for details.

## Pipeline Walkthrough

The entire pipeline is one function: `analyze_report(image_path)` in
[pipeline.py](pipeline.py). It's called by both the FastAPI endpoint and the
CLI entry point, so there's a single source of truth for "what does
analyzing a report actually do."

```python
def analyze_report(image_path: str) -> dict:
    biomarkers = extract_biomarkers(image_path)   # Stage 1: Vision LLM
    categorized = categorize(biomarkers)           # Stage 2: rule-based
    vector_store = load_vector_store()
    advice = generate_advice(categorized, vector_store)  # Stage 3+4: RAG
    return {"biomarkers": biomarkers, "categorized": categorized, "advice": advice}
```

## Stage 1 — Vision Extraction

**File:** [pipeline.py](pipeline.py) → `extract_biomarkers()`

This is a **multimodal / vision-language model (VLM)** call: the report
image is read as bytes, base64-encoded, and sent inline as an
`image_url` content block (using the `data:image/png;base64,...` scheme) in
a chat completion request — no OCR engine, no template matching, no
manual layout parsing.

The prompt is deliberately narrow to coax reliable **structured output**
out of a free-tier model that has no native JSON-mode / function-calling
guarantee:

```
This is a blood test report. Extract every biomarker name and its numeric value.

Respond with ONLY a JSON object, no other text, no markdown formatting, no code fences.
Format exactly like this example:
{"Hemoglobin": 15.0, "Platelet Count": 265}
```

The raw text response is parsed directly with `json.loads()`. This is a
classic **zero-shot extraction** pattern: no fine-tuning, no few-shot
examples beyond the one format example — just prompt-level constraint plus
strict downstream parsing. If parsing fails, that attempt counts as an
error and triggers the retry/fallback logic (see below).

## Stage 2 — Categorization

**File:** [categorize.py](categorize.py), [reference_ranges.py](reference_ranges.py)

This stage is **deliberately not AI**. Each biomarker value is compared
against a plain Python dict of min/max/unit reference ranges and tagged
`High`, `Low`, `Normal`, or `Unknown (no reference range)` if the extracted
name doesn't match anything in the table.

This is a conscious design choice: numeric threshold comparison is a
solved, deterministic problem, and using an LLM for it would add latency,
cost, and a non-zero hallucination risk for no benefit. Reserve the LLM for
the two things it's actually good at here — reading an image, and writing
fluent grounded prose.

## Stage 3 & 4 — RAG: Retrieval and Grounded Generation

This is the heart of the project's **Retrieval-Augmented Generation**
implementation, split across four files that mirror the classic RAG
pipeline stages: **load → chunk → embed → retrieve → generate**.

### Building the knowledge base (offline, one-time)

**File:** [build_vector_store.py](build_vector_store.py)

1. [load_articles.py](load_articles.py) reads every `.md` file in
   [articles/](articles/) — 14 short, hand-written articles, one per
   biomarker/condition (e.g. `anemia_low_hemoglobin.md`,
   `hypothyroidism_high_tsh.md`).
2. [chunker.py](chunker.py) splits each article into **overlapping,
   fixed-size word chunks** (60 words per chunk, 15-word overlap in the
   build script). The overlap exists so a chunk boundary doesn't cut a
   sentence's meaning in half — a small but important detail for retrieval
   quality.
3. [embedder.py](embedder.py) converts each chunk into an **embedding** — a
   dense vector representation of its meaning — via OpenRouter's
   `nvidia/llama-nemotron-embed-vl-1b-v2:free` embedding model.
4. Every `{article, chunk_index, text, embedding}` record is appended to a
   list and dumped to `vector_store.json`. This is the entire **vector
   store**: no database, no index structure beyond a flat list — simple by
   design, to keep the retrieval mechanics (next section) fully visible
   rather than hidden inside a library.

A 1-second sleep between embedding calls keeps the script within free-tier
rate limits.

### Retrieval

**File:** [retriever.py](retriever.py)

At query time, `retrieve_relevant_chunks(query, vector_store, top_k)`:

1. Embeds the query text using the same embedding model (queries and
   documents must live in the same embedding space to be comparable).
2. Computes **cosine similarity** between the query vector and every chunk
   embedding in the store — `dot(a, b) / (‖a‖ · ‖b‖)`, implemented directly
   with NumPy rather than a vector-DB's built-in similarity search.
3. Sorts and returns the `top_k` most similar chunks.

This is a brute-force, linear-scan **semantic search** — appropriate at
this scale (a few hundred chunks) and intentionally transparent, at the
cost of not scaling to a large corpus (see [Roadmap](#roadmap)).

### Grounded generation

**File:** [advisor.py](advisor.py) → `generate_advice()`

1. Filters the categorized biomarkers down to only `High`/`Low` (abnormal)
   findings. If none are abnormal, returns a canned "all normal" message
   with no LLM call at all.
2. For each abnormal biomarker, builds a query like `"Hemoglobin is Low"`
   and retrieves the single most relevant chunk (`top_k=1`) from the
   knowledge base.
3. Assembles a prompt containing: the findings summary, the retrieved
   context (clearly labeled per biomarker), and an explicit instruction to
   use **only** that context:

   ```
   Using ONLY the reference information above, write brief, general,
   educational guidance about these findings. Do not diagnose any
   condition. Do not recommend medications or dosages. Always end by
   recommending they consult a licensed doctor.
   ```

This is the **grounding** step of RAG: rather than letting the model answer
purely from its pretrained (parametric) knowledge — which for a health
topic carries real hallucination risk — its output is constrained to a
curated, reviewed knowledge base, with explicit guardrails against
diagnosis or medication advice baked directly into the prompt.

## Resilience: Retries & Multi-Model Fallback

Both LLM call sites — vision extraction ([pipeline.py](pipeline.py)) and
text generation ([advisor.py](advisor.py)) — iterate over an ordered list of
free-tier models:

```python
VISION_MODELS = [
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "google/gemma-4-26b-a4b-it:free",
]
```

For each model, the code retries a configurable number of times before
moving on to the next model in the list — in `advisor.py`, with a linear
backoff (`attempt * 5` seconds) between retries. This is a pragmatic
**graceful degradation** pattern for working against free-tier LLM APIs,
which are prone to rate limiting and intermittent unavailability: a single
model hiccup doesn't fail the whole request, it just costs a few seconds of
fallback latency.

The embedding call ([embedder.py](embedder.py)) has its own independent
retry loop (3 attempts, same backoff strategy) since it only ever uses one
embedding model.

## Mock Mode

Set `MOCK_AI=true` in `.env` to bypass every real model call:

- `extract_biomarkers()` returns `MOCK_BIOMARKERS` from
  [mock_data.py](mock_data.py) instead of calling the vision model.
- `generate_advice()` (invoked from `analyze_report()`) returns
  `MOCK_ADVICE` instead of calling the text model.

This lets you exercise the FastAPI endpoint end-to-end — upload, extraction,
categorization, advice — with zero network calls and zero rate-limit risk.
It's the fastest way to test a change or a new `/analyze-report` consumer
without burning free-tier quota.

## API Reference

**File:** [main.py](main.py)

### `GET /`

Health check. Returns `{"status": "Blood Report Analyser API is running"}`.

### `POST /analyze-report`

Accepts a `multipart/form-data` upload with a single field, `file`, that
must be an image (`Content-Type` starting with `image/`).

The uploaded file is written to a temporary file on disk (the pipeline
expects a file path, not raw bytes), passed through `analyze_report()`, and
the temp file is deleted afterward regardless of success or failure.

**Response body:**

```json
{
  "biomarkers": { "Hemoglobin": 10.6, "...": "..." },
  "categorized": {
    "Hemoglobin": { "value": 10.6, "status": "Low", "normal_range": "13.0–17.0 g/dL" }
  },
  "advice": "Your Hemoglobin is slightly below the typical range... (etc.) ...consult a licensed doctor."
}
```

**Error responses:**

- `400` — uploaded file is not an image.
- `500` — analysis failed (e.g. vision model returned unparseable output
  after exhausting all fallbacks, or embedding/generation failed).

CORS is currently wide open (`allow_origins=["*"]`) for local development —
this should be restricted to the actual consuming origin(s) before any
real deployment.

### `POST /upload`

Accepts a `multipart/form-data` upload with a single field, `file`, that
must be an image. Unlike `/analyze-report`, this endpoint does not run the
pipeline — it just saves the file to `uploads/` under a generated UUID
filename and returns a URL to it:

```json
{ "url": "/uploads/0cd76a6d-534d-4919-a4aa-27f6b85fe947.png" }
```

This exists so a client can hand the MCP server a stable, fetchable
**URL** for an image (see below), rather than passing raw image bytes
through the tool call.

## MCP Server & ChatGPT Integration

**File:** [mcp_server/server.py](mcp_server/server.py)

The pipeline is also exposed as a tool over the **Model Context Protocol
(MCP)**, using [FastMCP](https://github.com/jlowin/fastmcp), so any
MCP-compatible client — ChatGPT, Claude, or otherwise — can call it directly
as a tool during a conversation, instead of a human hitting the REST API.

```python
@mcp.tool
def analyze_blood_report(image_url: str) -> dict:
    ...
```

The tool takes an `image_url` rather than raw base64 bytes, since that's
the shape most MCP/agent clients pass a "here's an image" argument in. A
relative `/uploads/...` path is resolved against `BACKEND_API_URL`; the
image is then fetched with `httpx`, run through the exact same
`analyze_report()` pipeline used by `/analyze-report`, and the categorized
biomarkers + advice are returned as the tool result.

Rather than running as a standalone process, the FastMCP app is mounted
directly into the main FastAPI app in [main.py](main.py):

```python
mcp_app = mcp_server_instance.http_app(path="/")
app = FastAPI(title="Blood Report Analyser API", lifespan=mcp_app.lifespan)
app.mount("/mcp", mcp_app)
```

This keeps everything — the REST API, the uploaded-image static files, and
the MCP endpoint — behind a single port/process, so exposing the app
externally only requires one tunnel.

### Exposing it to a remote client (ChatGPT) via ngrok

ChatGPT's connector/tool setup needs a **public HTTPS URL**, both for the
MCP endpoint itself and for any image the tool is asked to fetch (a
`localhost` URL means nothing to ChatGPT's servers). For local development,
[ngrok](https://ngrok.com) bridges that gap by tunneling a public URL to the
local server:

```bash
uvicorn main:app --reload --port 8001
ngrok http 8001
```

ngrok prints a public forwarding URL, e.g.
`https://grievance-flatware-contently.ngrok-free.dev -> http://localhost:8001`
(a free ngrok URL like this is randomly generated per session and changes
every time the tunnel restarts). That URL is then registered as the
connector's MCP server URL in ChatGPT
(`https://<ngrok-subdomain>.ngrok-free.dev/mcp`).

End-to-end flow once connected:

1. Upload a report image via `POST /upload` (through the ngrok URL) to get
   back a public, fetchable image URL.
2. In a ChatGPT conversation, ask it to analyze the report at that URL.
   ChatGPT calls `analyze_blood_report(image_url=...)` on the connected
   MCP server.
3. The server fetches the image, runs the full pipeline, and returns the
   categorized biomarkers + advice — which ChatGPT then renders as a
   conversational answer.

This was verified working live: pointing ChatGPT at an uploaded report
through the ngrok tunnel returned a full categorized biomarker table (e.g.
Hemoglobin 10.6 g/dL — Low, WBC 13.8 ×10³/µL — High, Platelets 128 ×10³/µL —
Low) plus grounded, non-diagnostic guidance ending in a doctor-consult
recommendation — with the response correctly surfacing that it came from
`MOCK_AI` test-mode data.

## File-by-File Reference

| File | Role |
|---|---|
| [main.py](main.py) | FastAPI app, CORS config, `/analyze-report` + `/upload` endpoints, mounts MCP at `/mcp` |
| [mcp_server/server.py](mcp_server/server.py) | FastMCP server exposing `analyze_blood_report` as an MCP tool |
| [pipeline.py](pipeline.py) | `analyze_report()` orchestrator; vision extraction + model fallback list |
| [categorize.py](categorize.py) | Rule-based High/Low/Normal comparison |
| [reference_ranges.py](reference_ranges.py) | Biomarker → {min, max, unit} table |
| [load_articles.py](load_articles.py) | Reads all `.md` files from `articles/` into memory |
| [chunker.py](chunker.py) | Word-based overlapping text chunker |
| [embedder.py](embedder.py) | `embed_text()` — text → embedding vector, with retry |
| [build_vector_store.py](build_vector_store.py) | One-time script: chunk + embed every article → `vector_store.json` |
| [retriever.py](retriever.py) | `load_vector_store()`, cosine similarity, `retrieve_relevant_chunks()` |
| [advisor.py](advisor.py) | RAG prompt assembly + grounded advice generation, with model fallback |
| [mock_data.py](mock_data.py) | Canned biomarkers/advice for `MOCK_AI=true` |
| [articles/](articles/) | The RAG knowledge base — 14 biomarker/condition guidance articles |
| [uploads/](uploads/) | Images saved via `/upload`, for handing MCP clients a fetchable URL (gitignored) |
| [sample_report.png](sample_report.png) | Synthetic sample report image for manual testing |
| [playground.py](playground.py) | Scratch file for exploring snippets outside the main pipeline |

## Extending the Knowledge Base

To add coverage for a new biomarker or condition:

1. Add a new `.md` file to [articles/](articles/) with general, factual
   guidance (no diagnosis, no dosages — the generation prompt assumes the
   source material is itself safe to surface directly).
2. Add its reference range to `REFERENCE_RANGES` in
   [reference_ranges.py](reference_ranges.py), if you want it categorized
   rather than falling into `Unknown (no reference range)`.
3. Re-run `python3 build_vector_store.py` to re-chunk and re-embed
   everything (it's a full rebuild, not incremental).

## Roadmap

- [x] Vision-based biomarker extraction (multimodal LLM)
- [x] Rule-based categorization
- [x] RAG knowledge base (chunking, embeddings, retrieval, generation)
- [x] Rate-limit resilience (retry + multi-model fallback)
- [x] FastAPI service wrapping the pipeline
- [x] MCP server exposing the pipeline as a tool (`analyze_blood_report`),
      verified working end-to-end with ChatGPT via an ngrok tunnel
- [ ] Restrict CORS to actual consuming origin(s) before any deployment
- [ ] Deploy the API/MCP server behind a stable public URL instead of an
      ephemeral ngrok tunnel
- [ ] Incremental vector-store updates (currently a full rebuild per run)
- [ ] Swap the flat JSON vector store + linear cosine scan for a real
      vector database once the knowledge base grows meaningfully past a
      few dozen articles
- [ ] Structured output via function-calling / JSON mode, where the
      chosen model supports it, instead of prompt-only JSON constraints
- [ ] Automated tests (unit tests for `categorize`/`chunker`/`retriever`;
      integration tests against `MOCK_AI=true`)
- [ ] Evaluation harness for retrieval relevance and generation groundedness
- [ ] Structured logging in place of `print()` statements

## Disclaimer

This project generates general, educational health information only. It does
not diagnose conditions, recommend medications or dosages, and is not a
substitute for professional medical advice. Always consult a licensed doctor
to interpret real blood test results.
