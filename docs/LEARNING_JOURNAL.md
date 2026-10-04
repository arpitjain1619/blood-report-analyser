# LEARNING_JOURNAL.md

> A personal, beginner-friendly learning record for the Health Report Analyzer
> project (formerly Blood Report Analyser). Written **to learn from** — each entry
> is a small lesson, not a terse note. Structure per entry:
>
> **What is it → Why it exists / why we use it → How it works → How we use it in
> this project → Takeaway.**
>
> Scope: AI-engineering, Python, and React concepts only. Pure plumbing lessons
> (ports, virtualenv, machine setup, tunnels) are deliberately left out.
>
> Entries tagged *Learned in conversation* were worked through live while building.
> Dates are mostly Unknown — the record didn't reliably timestamp each moment.
> Model IDs and library specifics are volatile config, not fixed architecture.

---

## Table of contents

**AI / RAG**
1. RAG (Retrieval-Augmented Generation) — the core idea
2. When RAG is *not* the right tool
3. Embeddings and vector stores
4. Chunking
5. Vision LLMs and structured output
6. Prompt engineering for reliable structured output
7. Grounding advice so the model can't make things up
8. Retry, backoff, and multi-model fallback
9. Applying resilience to *every* AI call, not just the first

**MCP (Model Context Protocol)**
10. What MCP is and why it matters
11. MCP transports: stdio vs. Streamable HTTP
12. Why large binary payloads break MCP tool calls

**Python**
13. Calling different providers with one SDK (provider abstraction)
14. ASGI, and mounting one app inside another (shared lifespans)
15. Defensive parsing and cleanup with try / finally

**React**
16. How the frontend is structured (components + state + fetch)
17. Vite environment variables (and why the base URL shouldn't be hardcoded)

**Provider migration (learned in conversation)**
18. Provider APIs are not interchangeable (OpenAI-style vs. Anthropic)
19. Not every provider offers every capability (the embeddings gap)
20. Vision message formats differ between providers
21. Embedding dimensions are provider-specific (and force a re-index)
22. getenv returns None silently — a typo'd env var name fails quietly

**Designing for change (learned in conversation)**
23. Designing a schema for the future without breaking the present
24. Why mock mode returns the same *shape* as real mode
25. Rule-based classification with set intersection (and why not AI)
26. Reference data as *data*, not code (JSON over hardcoding)

**Modelling real-world domain data (learned in conversation)**
27. One output shape over many input kinds (range / direction / bands)
28. Keeping error/edge states honest instead of guessing
29. Precedence and provenance: whose number wins, and saying so
30. Defensive parsing of messy real-world strings

**RAG at scale, and meeting reality (learned in conversation)**
31. Metadata-filtered retrieval (keeping RAG results on-topic)
32. Carrying metadata through the pipeline (thread-through)
33. AI-generated domain content and the human-review gate
34. Mock testing can't catch real-model misbehavior (the JSON-fence lesson)

**Structured output, safety framing, and resilience (learned in conversation)**
35. Structured output from an LLM (and why you parse it defensively)
36. Guarantee safety-critical things in code, not in the prompt
37. Grading severity: mild-abnormal vs. critical (and calibrating to avoid false alarms)
38. Graceful partial failure (keep the good, report the bad)

**Handling messy multi-part input (learned in conversation)**
39. Splitting one input into multiple sections (and the "confident vs. isolated" line)
40. Challenging a decision from both sides before committing
41. Removing orphan code (and verifying before you delete)

**Contracts, per-person data, and knowing where to stop (learned in conversation)**
42. A tool's description is a contract (and it can go stale while the code is fine)
43. Personalizing by a per-person attribute (precedence + reading sensitive data)
44. Deciding where the tool should stop (explain, don't interpret)

**Refactoring a growing codebase (learned in conversation)**
45. Single-responsibility: splitting modules that grew too many jobs
46. Python packages & absolute imports (and entry-points-at-root)
47. Where a file looks for its data (`__file__` vs. working directory)
48. Grep exhaustively before you edit (don't trust your memory of the code)
49. Surgical rename: renaming the project without breaking a domain term
50. A virtualenv bakes in its own path (so a folder rename breaks it)

---

# AI / RAG

## 1. RAG (Retrieval-Augmented Generation) — the core idea

**Date:** Unknown

### What is it?
RAG is a pattern where, instead of asking an AI model a question straight away,
you first look up relevant information yourself, then hand that information to the
model and ask it to answer using only what you gave it. "Retrieval" = finding the
right text; "Augmented" = adding it to the prompt; "Generation" = the model
writing the answer.

### Why does it exist / why use it?
A language model only knows what it saw in training. Ask it about a specific
document it never saw and it will often guess confidently ("hallucinate"). RAG
makes sure the model answers from real, provided source material rather than vague
memory.

### How does it work?
Three steps: search a knowledge base for the chunks most relevant to the question;
paste those chunks into the prompt as context; instruct the model to answer only
from that context. The search is usually meaning-based (embeddings), not keyword.

### How we use it in this project
When a biomarker is abnormal, we retrieve the relevant chunk from our knowledge
base and ask the model to explain using only that — the RAG stack
(load_articles, chunker, embedder, retriever, advisor).

### Takeaway
RAG is two independent machines — a search engine and a text generator — bolted
together. You need it when the knowledge is too big or unstructured to just paste
in every time.

### Analogy that helped
A well-spoken friend who's never read your storybook: instead of asking cold, you
find the relevant pages first and say "answer using only these."

---

## 2. When RAG is *not* the right tool

**Date:** Unknown

### What is it?
Recognizing that some lookup problems are too small or too structured to need
retrieval at all.

### Why does it matter?
RAG adds real moving parts (embeddings, a vector store, a search step). If your
knowledge is a small fixed table, that machinery is wasted — plain code is simpler,
faster, free, more reliable.

### How does it work?
Ask: is the knowledge large or unstructured? If yes → RAG earns its place. If it's
a short structured lookup table → just use a dict/comparison, or hand the whole
table to the model.

### How we use it in this project
Biomarker reference ranges are a small fixed table, so categorization is plain
Python comparison — not RAG, not even an AI call. RAG is reserved for the
open-ended "explain this abnormal finding" step.

### Takeaway
Match the technique to the shape of the problem. Sophisticated ≠ correct.

---

## 3. Embeddings and vector stores

**Date:** Unknown

### What is it?
An embedding is a list of numbers representing the *meaning* of text as a point in
high-dimensional space. Similar meaning → nearby points. A vector store is a
collection of {text, numbers} pairs you can search.

### Why does it exist / why use it?
Computers can't compare meaning directly, and keyword matching is dumb ("low
hemoglobin" vs "anemia" share no words but are related). Embeddings turn meaning
into geometry, so "find the most related text" becomes "find the nearest points."

### How does it work?
Send text to an embedding model, get its vector. To search, embed the query too,
then measure closeness to each stored vector (cosine similarity — the angle
between them). Smallest angle = most similar. No single number means anything
alone; meaning lives in the whole pattern.

### How we use it in this project
embedder.py turns each knowledge chunk into a vector; build_vector_store saves
them to vector_store.json; retriever embeds the query and cosine-searches.

### Takeaway
Embeddings are the bridge from words to math — what makes semantic search possible.

---

## 4. Chunking

**Date:** Unknown

### What is it?
Splitting a document into smaller, often overlapping pieces before embedding it.

### Why does it exist / why use it?
Two reasons: a whole document may be too big for the context window, and a
multi-topic document embeds better in focused pieces. Overlap stops an idea being
sliced in half at a boundary.

### How does it work?
Walk the text in windows of N words; each new window starts a little before the
previous ended (the overlap). The tail of one chunk reappears at the head of the
next.

### How we use it in this project
chunker.py's chunk_text(text, chunk_size, overlap); the store was built with
60-word chunks / 15-word overlap. Our articles are short enough not to strictly
need it — we did it for practice.

### Takeaway
Chunking solves specific problems (size + mixed topics). Not a mandatory step of
RAG, but worth practising deliberately.

---

## 5. Vision LLMs and structured output

**Date:** Unknown

### What is it?
A vision LLM accepts an image as input and can reason about it. Structured output
means getting the answer in a strict machine-readable format (JSON), not prose.

### Why does it exist / why use it?
We need clean {name: value} data out of a report photo. A prose description is
useless to the rest of the pipeline, which needs predictable structured data.

### How does it work?
The image is base64-encoded and sent as part of a multimodal message (a content
list mixing text and image parts, not a single string). You prompt for a strict
format and parse the reply.

### How we use it in this project
Stage 1 of pipeline.py (extract_biomarkers) sends the report image plus a
"respond with ONLY JSON" instruction to a vision model, then json.loads the result.

### Takeaway
The message shape for images differs from text-only calls, and asking for
structured output is a real technique, not an afterthought.

---

## 6. Prompt engineering for reliable structured output

**Date:** Unknown

### What is it?
Deliberately wording a prompt so the model's output is reliable and usable — here,
returning only clean JSON.

### Why does it exist / why use it?
Models are eager to be chatty. Ask loosely and you get "Sure! Here's the data:"
plus JSON in code fences, which breaks json.loads. Small wording changes produce
big reliability differences.

### How does it work?
Be explicit and *show* the shape. "Respond with ONLY a JSON object, no other text"
plus a concrete example dramatically improves the hit rate. Still parse
defensively — models don't obey perfectly.

### How we use it in this project
The extraction prompt demands JSON-only and shows an example structure. When we
later added units/ranges (HRA-07), the concrete nested example did the heavy
lifting for the richer shape.

### Takeaway
Prompt wording is engineering, not fluff. Be explicit, show an example, never fully
trust the format — validate it.

---

## 7. Grounding advice so the model can't make things up

**Date:** Unknown

### What is it?
Forcing the model to build its answer only from source material you supply, not its
own general knowledge.

### Why does it exist / why use it?
For a health-adjacent product this is safety-critical — we don't want invented
medical claims. If the model can only speak from vetted articles, output is far
more controllable; when no article exists, it falls back to generic guidance
instead of bluffing.

### How does it work?
The prompt includes retrieved context plus explicit instructions: use ONLY this
context, don't diagnose, don't name meds/dosages, always recommend a doctor. Safety
rules live in the prompt *and* the article content, not the model's discretion.

### How we use it in this project
advisor.py filters to abnormal findings, retrieves per-biomarker context, builds
one grounding prompt. A real test (low platelet, no article) gave only generic
guidance — the desired behavior.

### Takeaway
Grounding is the safety backbone of RAG. "Use only what I gave you" meaningfully
changes behavior.

---

## 8. Retry, backoff, and multi-model fallback

**Date:** Unknown

### What is it?
Patterns for surviving flaky external AI APIs: retry (try again), backoff (wait
longer between tries), fallback (if one model fails, try another).

### Why does it exist / why use it?
Providers fail often, and two different failures can look identical (both HTTP
429): per-model congestion (a different model can succeed — fallback helps) vs. an
account-wide daily cap (switching models does nothing — only waiting/quota helps).

### How does it work?
Loop over models: try A; on failure wait and/or move to B, then C. Read the actual
error payload, not just the status code, to know which 429 you're facing.

### How we use it in this project
Vision and advice both walk a model list until one works
(call_model_with_fallback). We hit both 429 types for real.

### Takeaway
Two failures that look the same can need opposite fixes. Read the error body, not
just the number.

---

## 9. Applying resilience to *every* AI call, not just the first

**Date:** Unknown

### What is it?
Making sure retry/fallback/timeout/validation is on every function that calls an
external AI API, consistently.

### Why does it matter?
We built resilience into vision first, then a run crashed in advisor.py, which had
no protection. An audit found embedder.py unprotected too. Cross-cutting concerns
have to be applied system-wide.

### How does it work?
Treat "makes an external AI call" as a checklist trigger; factor the pattern into a
shared helper so it's easy to apply and hard to forget. (Formalized later as an
HRA-04 Definition-of-Done item.)

### How we use it in this project
call_model_with_fallback across extraction, advice, and (retry-only) embeddings.
One honest gap: embeddings have retry but no fallback model.

### Takeaway
The first place you build a cross-cutting concern is rarely the only place that
needs it.

---

# MCP (Model Context Protocol)

## 10. What MCP is and why it matters

**Date:** Unknown

### What is it?
A standard way for an AI assistant to call real code/tools during a conversation,
not just produce text. A server exposes "tools" (name, description, typed I/O); a
client discovers and calls them.

### Why does it exist / why use it?
Without it an AI can only *talk about* your report. With MCP, ChatGPT can actually
run your real pipeline and answer from true results.

### How does it work?
In FastMCP, a decorator (@mcp.tool) turns a Python function into a tool. Its type
hints generate the schema; its docstring is what the AI reads to decide when/how to
use it — so the docstring is a real design and safety surface.

### How we use it in this project
analyze_blood_report wraps analyze_report directly (no HTTP hop). Tested first in
the MCP Inspector before ChatGPT. (In HRA-03 we updated the docstring so the AI
knows PDFs are accepted too — that wording is functional, not decoration.)

### Takeaway
A docstring is the model's instruction manual for the tool. Test tools in isolation
before facing a messy real client.

---

## 11. MCP transports: stdio vs. Streamable HTTP

**Date:** Unknown

### What is it?
How client and server talk. stdio = client launches the server as a local
subprocess on the same machine. Streamable HTTP = server runs as a networked
service with a URL.

### Why does it matter?
It decides who can reach the server. stdio only works for a same-machine client; a
cloud client like ChatGPT needs a real remote HTTP URL.

### How does it work?
You pick the transport when running the server. Same tool code, different reach;
remote clients also need the URL exposed publicly.

### How we use it in this project
Started on stdio (fine for Inspector), switched to streamable-http for ChatGPT.

### Takeaway
Choose transport by where the *client* runs, not what's easiest locally first.

---

## 12. Why large binary payloads break MCP tool calls

**Date:** Unknown

### What is it?
Stuffing a big base64 blob (an image) directly into an MCP tool *argument* is a
known fragile spot across the MCP ecosystem.

### Why does it matter?
The first design, analyze_blood_report(image_base64), hung ChatGPT's client before
the request even reached the server, on an 83KB image. MCP's native image type was
also badly handled by ChatGPT specifically.

### How does it work / what's the fix?
Don't send bytes through the argument. Pass a URL; the server fetches the file
itself over HTTP. Mirrors the real "upload to storage, pass a link" pattern.
Trade-off: the server must be able to reach the URL.

### How we use it in this project
The tool takes a URL; the server fetches with httpx, writes a temp file, runs the
pipeline, deletes the temp file. (HRA-03 extended this to derive the temp file's
extension from the URL, so PDFs reach the right pipeline branch.)

### Takeaway
Even the "correct" protocol-native way can be broken in a specific client. A
pragmatic workaround can beat chasing the proper way.

---

# Python

## 13. Calling different providers with one SDK (provider abstraction)

**Date:** Unknown

### What is it?
Using one client library to talk to multiple providers by pointing it at a
different base URL.

### Why does it exist / why use it?
Many providers copy the OpenAI API shape, so the same SDK can talk to a different
service just by changing where it points — handy when a provider's key stops
working and you need to switch fast.

### How does it work?
Create the OpenAI client with base_url set to the other provider's endpoint (and
its key). Method calls stay the same because request/response shapes match.

### How we use it in this project
We used the OpenAI SDK pointed at OpenRouter for all calls — until we later moved
off it entirely (see entries 18–21).

### Takeaway
A shared API shape makes provider swaps a config change, not a rewrite — *when* the
shapes actually match (they don't always — see entry 18).

---

## 14. ASGI, and mounting one app inside another (shared lifespans)

**Date:** Unknown

### What is it?
ASGI is the standard interface async Python web apps (FastAPI) use to talk to a
server (Uvicorn). Because both the FastAPI backend and the FastMCP server are ASGI
apps, one can be mounted inside the other at a URL prefix.

### Why does it exist / why use it?
We needed the API and the MCP server both publicly reachable at once, but the free
tunnel allowed only one. Merging them into one process/port meant one tunnel
covered both — an architecture fix for an infra limit.

### How does it work?
app.mount("/mcp", mcp_app). The subtlety: the sub-app's lifespan (startup/shutdown
hook) must be wired into the parent at creation time
(FastAPI(lifespan=mcp_app.lifespan)) or MCP session handling breaks obscurely.

### How we use it in this project
main.py builds the MCP app, passes its lifespan to the parent, mounts at /mcp.

### Takeaway
When nesting one framework's app in another, check for lifecycle-hook wiring, not
just routes — that's the easy-to-miss critical part.

---

## 15. Defensive parsing and cleanup with try / finally

**Date:** Unknown

### What is it?
Never assume an external response is well-formed before parsing it, and always
clean up temp resources whether or not things succeeded.

### Why does it exist / why use it?
An AI call can return empty/malformed content; json.loads on it crashes. Temp files
leak if an error skips cleanup. finally runs no matter what.

### How does it work?
Validate the response before parsing. Put cleanup (os.remove) in finally. After
exhausting retries, re-raise the real error rather than swallowing it.

### How we use it in this project
Extraction validates before json.loads. Endpoints and the MCP tool delete temp
files in finally. The PDF helper cleans up per-page temp images in finally too
(HRA-03).

### Takeaway
Assume external data is hostile until validated, and tie cleanup to finally so an
error path can't skip it.

---

# React

## 16. How the frontend is structured (components + state + fetch)

**Date:** Unknown

### What is it?
A tree of components, with one component owning the state and passing data down,
and a fetch call to talk to the backend.

### Why is it built this way?
React favours small focused pieces and keeping mutable data ("state") in one clear
owner, so the UI re-renders predictably when it changes.

### How does it work?
main.jsx boots the app → App.jsx renders Header + Body. Body.jsx holds
{image, result} via useState, builds FormData, fetch-POSTs to /analyze-report,
stores the reply with setResult. State change → re-render → Result.jsx shows
Table.jsx plus advice.

### How we use it in this project
The upload-and-show-results flow. State lives in Body.jsx; children receive and
render. (Frontend updates for the new backend shapes are a tracked follow-up.)

### Takeaway
One component owns state; children display it. useState + re-render is the core
loop of a React UI.

---

## 17. Vite environment variables (and why the base URL shouldn't be hardcoded)

**Date:** Unknown

### What is it?
Vite is the frontend build tool/dev server (chosen over the deprecated Create React
App). It exposes only variables prefixed VITE_ to app code, read via
import.meta.env.VITE_SOMETHING.

### Why does it matter?
Hardcoding the backend URL in a component is brittle — it caused a real bug where
frontend and backend pointed at different ports and silently never connected. An
env var keeps that setting in one place and lets it differ between dev and
deployment.

### How does it work?
Put VITE_API_BASE_URL in a .env file; Vite bakes it in at build time; the component
reads import.meta.env.VITE_API_BASE_URL. The VITE_ prefix is required (a safety
default so secrets aren't leaked to the browser).

### How we use it in this project
The fix for the port mismatch: drive the backend base URL from a Vite env var
rather than a hardcoded string.

### Takeaway
In Vite, client-exposed env vars must start with VITE_ and are injected at build
time. Config like a base URL belongs in an env var, never hardcoded.

---

# Provider migration (learned in conversation)

## 18. Provider APIs are not interchangeable (OpenAI-style vs. Anthropic)

**Date:** Unknown · *Learned in conversation*

### What is it?
Different providers expose different API shapes — method names, required params,
response structures — even doing the "same" thing.

### Why does it matter?
"Switching providers = change the model name" is false. Moving advice generation
from OpenRouter (OpenAI SDK) to Anthropic required rewriting the call, not
re-pointing it.

### How does it work? (the concrete differences)
- Method: client.chat.completions.create → client.messages.create.
- max_tokens is REQUIRED on Anthropic; optional on OpenAI. Biggest gotcha.
- Response: response.choices[0].message.content → response.content[0].text.
- Client: no base_url needed (Anthropic's own SDK talking to Anthropic).
- System prompt: Anthropic uses a top-level system= param, not a role:"system"
  message.

### How we use it in this project
advisor.py and pipeline.py switched from the OpenAI SDK to the anthropic SDK — same
logic, rewritten call shape.

### Takeaway
"Switch providers" is a code change, not a config change. Check the docs rather than
assuming parity.

---

## 19. Not every provider offers every capability (the embeddings gap)

**Date:** Unknown · *Learned in conversation*

### What is it?
A provider you like may simply not offer a capability you need — Anthropic provides
no embedding model at all.

### Why does it matter?
The plan was "use Claude for everything." But RAG needs embeddings, and there's no
Claude embedding model — so embeddings *had* to go to a different provider.

### How does it work?
You end up with a multi-provider architecture (normal in real systems): one
provider for generation, another for embeddings. Each with its own SDK, key, env
var.

### How we use it in this project
Text + vision → Anthropic; embeddings → Google Gemini. Three AI calls, two
providers.

### Takeaway
Before committing to "provider X for everything," check X offers *every* capability
you need. Mixing providers is normal, not failure.

---

## 20. Vision message formats differ between providers

**Date:** Unknown · *Learned in conversation*

### What is it?
How you attach an image to a request is provider-specific.

### Why does it matter?
Vision was the trickiest migration piece — not a rename, a differently-structured
payload, so a copy-paste of the old message body silently wouldn't work.

### How does it work? (the two shapes)
- OpenAI-style: {"type":"image_url","image_url":{"url":"data:image/png;base64,<DATA>"}}
  — a data URL string with media type in the prefix.
- Anthropic: {"type":"image","source":{"type":"base64","media_type":"image/png","data":"<DATA>"}}
  — fields broken out; data is the RAW base64 with NO data: prefix.

### How we use it in this project
extract_biomarkers sends the report image as an Anthropic image block. The text
block was identical between SDKs; only the image block changed.

### Takeaway
For multimodal requests, image format is provider-specific. Watch whether it wants
a full data-URL or raw base64 + a separate media_type.

---

## 21. Embedding dimensions are provider-specific (and force a re-index)

**Date:** Unknown · *Learned in conversation*

### What is it?
Different embedding models output vectors of different lengths. Old OpenRouter model
= 2048-dim; Gemini = 3072-dim.

### Why does it matter?
Retrieval compares a query vector against stored vectors (cosine similarity). That
math only works if both have the *same* dimension. Change models and every stored
vector is the wrong size — the old store becomes unusable.

### How does it work?
Whenever the embedding model changes, regenerate the entire vector store. You can't
mix vectors from two models.

### How we use it in this project
After switching embedder.py to Gemini, we deleted vector_store.json and re-ran
build_vector_store — which doubled as the first real Gemini test (one batch run
instead of many small ones, kind to quota).

### Takeaway
Changing your embedding model invalidates your whole vector store. Always delete and
rebuild after a swap; query and documents must be embedded by the same model.

---

## 22. getenv returns None silently — a typo'd env var name fails quietly

**Date:** Unknown · *Learned in conversation*

### What is it?
os.getenv("NAME") returns None when the variable isn't found — it does NOT raise.
So a misspelled name fails silently and blows up later, somewhere less obvious.

### Why does it matter?
We chased a "No API key was provided" crash from the Gemini client. Real cause:
.env had GEMENI_API_KEY (typo) while the code read GEMINI_API_KEY. getenv returned
None; the error surfaced deep in the SDK, far from the typo.

### How does it work? (the debugging move)
Isolate config from logic. A no-network one-liner proved where the problem was
without spending quota:
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print(repr(os.getenv('GEMINI_API_KEY')))"
None → name/spelling wrong or .env not found. A real string → key loads. repr()
also reveals stray quotes/whitespace.

### How we use it in this project
Confirmed the name matched between .env and code, fixed the spelling, Gemini
authenticated.

### Takeaway
A missing env var doesn't announce itself. Suspect name/spelling first, and verify
config in isolation (no API call) before blaming the key or the code.

---

# Designing for change (learned in conversation)

## 23. Designing a schema for the future without breaking the present

**Date:** Unknown · *Learned in conversation*

### What is it?
Changing the *shape* of the data the pipeline passes around to support things you
don't build yet (many report types, narrative findings) while keeping today's flow
working.

### Why does it matter?
The blood-only pipeline returned a dict keyed by biomarker name. To generalize it
needs to also carry findings with no number (a radiology sentence). Design only for
today and every future type forces a disruptive rewrite; design with *room* now and
later stories slot in.

### How does it work?
We replaced name-keyed dicts with a list of typed entries, each declaring a kind
("numeric" / "narrative") — a discriminator field that tells consuming code which
kind it's looking at. Consumers guard on kind == "numeric" *now*, even before any
narrative entries exist, so nothing breaks when they appear.

### How we use it in this project (HRA-01)
categorize returns the list; analyze_report returns {report_type, findings,
advice}; advisor and CLI filter by kind.

### A key judgment call
We chose the fuller unified list over a smaller additive change *because it's a
learning project and the clean foundation was worth it*. In production you'd weigh
"cost of the big change now" against "how soon you need the capability." Design for
change; don't gold-plate for a future you may never reach.

### Takeaway
Add room for what's coming (a discriminator, a flexible container) and make today's
code tolerate it — but don't fully build capabilities you won't use for many steps.

---

## 24. Why mock mode returns the same *shape* as real mode

**Date:** Unknown · *Learned in conversation*

### What is it?
Understanding *where* the mock/real switch happens, and why that guarantees
identical output shape.

### Why does it matter?
Mock mode tests structure without paying for AI calls — which only works if mock
output has the same shape as real output.

### How does it work?
MOCK_AI only swaps the two expensive AI calls (extraction, advice). Everything
around them — categorization and the return-assembly — is shared. Both paths produce
a {name: value} dict at the same midpoint, then run the *same* categorize and *same*
return-assembly. The shape is built by shared code, so it can't diverge.

### How we use it in this project
We kept MOCK_BIOMARKERS as the pipeline's *input* and let real categorize build the
output shape. Mock mode thus exercises real categorization code, and there's no
second copy of the output shape to drift.

### Takeaway
Mock at the *input* boundary and let real downstream code build the output. Then
mock and real share the shape-building code and can't disagree — and you test more
real code for free.

---

## 25. Rule-based classification with set intersection (and why not AI)

**Date:** Unknown · *Learned in conversation*

### What is it?
Deciding what *kind* of report an upload is by plain set matching — comparing
extracted marker names against known "signature" markers per type — not by asking a
model.

### Why does it matter?
Classification sounds like an AI job. But if you already have the signals (extracted
names) and a known mapping, plain code gives one correct, instant, free answer — no
model, no cost, no unpredictability.

### How does it work?
A set is an unordered collection of unique items; Python intersects two sets with &.
extracted_names & signatures gives the overlap; len(...) is the match count. Require
a minimum (we used 2) to avoid a single stray name triggering a match; if nothing
clears the bar, return "unknown" rather than guess; when several match, most overlap
wins.

### How we use it in this project (HRA-02)
detect_report_type reads report definitions and does this intersection to set
report_type for real. No AI call. "unknown" is a valid, honest result.

### Takeaway
Before reaching for a model: "do I already have the signal, and is there one correct
answer?" If yes, plain code is cheaper and more reliable. Always leave an honest
"unknown" escape hatch.

---

## 26. Reference data as *data*, not code (JSON over hardcoding)

**Date:** Unknown · *Learned in conversation*

### What is it?
Keeping domain data (markers, ranges, which markers signal which type) in data files
(JSON) the code loads, not baked into Python as dicts.

### Why does it matter?
Starting with 19 blood markers in a Python dict is fine for one type. Scaling to
many types would turn code files into giant data dumps, painful to edit, and every
new test would mean editing *code* for what's really *data*.

### How does it work?
Domain facts in a .json file organized by report type; a small loader reads them.
Code stays about logic; the file about facts. A future swap to an authoritative
external source then changes only the *loader*.

### How we use it in this project
report_data.json holds each report type's signature markers *and* ranges (DEC-020).
Recorded that in-repo JSON is for now, with an external authoritative medical source
as the long-term direction.

### The honest caveat
In-repo hand-curated medical data can drift from real clinical values. Accepted for
this stage, not forever — a real product leans on a maintained source.

### Takeaway
Treat data as data. Domain facts in data files, logic in code. Scales better,
easier to edit, and makes swapping the source a one-place change — just stay honest
about hand-curated data's limits for health.

---

# Modelling real-world domain data (learned in conversation)

## 27. One output shape over many input kinds (range / direction / bands)

**Date:** Unknown · *Learned in conversation*

### What is it?
Different medical markers need different judgment styles, but downstream code should
see one uniform result shape.

### Why does it matter?
Hemoglobin has a normal *band* (too-low and too-high both matter). LDL is
one-sided (only too-high matters). HbA1c has *named tiers* (Normal / Prediabetes /
Diabetes). If every consumer had to know each marker's style, complexity would leak
everywhere.

### How does it work?
Each marker declares a kind in the data: "range", "direction", or "bands".
categorize has one branch per kind — but they all emit the *same* fields: a human
status/label AND a uniform severity ("normal" / "attention" / "unassessed"). So the
advisor, CLI, and frontend only ever read severity to decide "is this worth
flagging," never needing to know the marker's kind.

### How we use it in this project (HRA-06)
categorize(biomarkers, report_type) reads per-type ranges from report_data.json and
handles all three kinds. Diabetes/lipids use bands; Vitamin D uses direction; CBC
and thyroid use range.

### Takeaway
Let inputs be as varied as reality demands, but collapse them to one consistent
output shape. A discriminator ("kind") in the data plus a uniform result field
(severity) keeps the varied logic from spreading into every consumer.

---

## 28. Keeping error/edge states honest instead of guessing

**Date:** Unknown · *Learned in conversation*

### What is it?
When the system can't confidently do something, say so plainly rather than
fabricate a plausible-looking result.

### Why does it matter?
For a health tool, a confident wrong answer is worse than an honest "can't assess."
Two cases came up: an unrecognized report type, and a marker with no reference
range.

### How does it work?
- Unknown report type → short-circuit before categorize/advice; return the normal
  {report_type, findings, advice} shape with report_type "unknown", empty findings,
  and an honest "unsupported" message (HRA-05). Consistent shape means no consumer
  needs a special code path — "unknown" + empty findings *is* the signal.
- Unknown marker → status "Unknown (no reference range)", severity "unassessed"
  (its own value, distinct from normal/attention), so the advisor ignores it and
  the UI can show "couldn't evaluate" — not a quiet lie that it's normal, not a
  false alarm.

### How we use it in this project
HRA-05's early return, and the "unassessed" severity in categorize.

### Takeaway
Design explicit honest states for "can't do this." Keep their shape consistent with
success so nothing downstream special-cases them, and don't flatten "not assessed"
into "normal" — that's a quiet lie.

---

## 29. Precedence and provenance: whose number wins, and saying so

**Date:** Unknown · *Learned in conversation*

### What is it?
When two sources of truth exist (the range printed on the report vs. our own
reference data), deciding which one judgment uses — and recording which was used.

### Why does it matter?
A lab's printed range is authoritative for *that* report; our JSON range is
illustrative. So the report's range should usually win. But a printed low-high can't
express named tiers (Prediabetes/Diabetes), so for band markers our richer model is
better. The rule can't be flat.

### How does it work?
Precedence (HRA-07): for range-kind markers, prefer the report's printed range when
it parses; else fall back to JSON. For bands/direction, always use JSON (a printed
low-high would lose the tiers). Always *capture and display* the printed unit/range
regardless. And add a provenance field (range_source: "report"/"data"/"none") so
it's visible which source judged each value.

### How we use it in this project
categorize applies this precedence and stamps range_source on every finding; the
CLI shows "via: report/data" so you can see the source at a glance.

### Takeaway
When multiple sources of truth exist, make precedence explicit and *record
provenance*. "Which number did we use, and where did it come from" is information
users (and debuggers) deserve — especially in a health tool.

---

## 30. Defensive parsing of messy real-world strings

**Date:** Unknown · *Learned in conversation*

### What is it?
Turning inconsistent human/lab-formatted strings (printed ranges) into usable
numbers, without crashing on the ones you can't handle.

### Why does it matter?
Labs print ranges every which way: "13.0-17.0", "13.0 – 17.0" (en-dash), "<200",
">40", "≤ 100", or "Negative". Code that assumes one format breaks on the rest — and
in a health tool a parsing crash or a misread range has real cost.

### How does it work?
Normalize variants first (en/em dashes → hyphen; ≤/≥ → <=/>=). Handle two-sided
(low-high) and one-sided (<X, >X) formats, returning (min, max) where either bound
may be None for one-sided. Anything unparseable returns None → graceful fallback to
the other source, never a crash. Test the operator order carefully (check "<=" before
"<"). One-sided printed ranges and JSON "direction" markers then share the same
"open bound = skip that check" logic.

### How we use it in this project (HRA-07)
_parse_printed_range handles all those formats; _categorize_printed_range judges
against the parsed bounds, skipping a check when its bound is None. Unparseable →
fall back to JSON.

### The honest note
We verified each path with purpose-built inputs (two-sided AND one-sided), because
code you write but never *run* harbors quiet bugs — the same lesson as a typo that
only surfaces when its line executes.

### Takeaway
Real-world input is messy; parse defensively, normalize variants, and always have a
graceful fallback for what you can't handle. Then actually *run* every branch — don't
trust unparsed-but-unrun code.

---

# RAG at scale, and meeting reality (learned in conversation)

> These come from growing the knowledge base to many report types (HRA-11),
> filtering retrieval by type (HRA-12), and finally running the whole thing on a
> real PDF for the first time — which surfaced a real bug that mock testing never
> could.

## 31. Metadata-filtered retrieval (keeping RAG results on-topic)

**Date:** Unknown · *Learned in conversation*

### What is it?
Attaching a label (metadata) to each stored chunk and, at query time, only
searching chunks whose label matches — so retrieval can't wander off-topic.

### Why does it matter?
Plain semantic search compares the query against *every* chunk. Once the knowledge
base spans many report types, a query about a lipid finding could pull a
thyroid or blood chunk if it happened to score high — and grounding advice on the
wrong report's content is exactly the kind of error a health tool must not make.

### How does it work?
Each chunk carries a `type` tag (added when the vector store is built). At query
time, before scoring by similarity, filter the candidate chunks down to only those
whose `type` matches the report — a "hard filter." Then score just those. If the
filter leaves *nothing*, return nothing and let the caller fall back to generic
guidance (rather than searching everything and risking a wrong-type match — the
one case you're least able to ground well). A nice side effect: an empty filter
skips the query-embedding call entirely, saving cost.

### How we use it in this project (HRA-12)
`retrieve_relevant_chunks` takes a `report_type`; it filters the vector store to
that type's chunks before scoring. Proven with a sharp test: the *same* "LDL is
high" query returns the LDL article when filtered to `lipid`, but returns thyroid
articles (never the LDL one) when filtered to `thyroid`. Same query, different
filter, completely type-appropriate results.

### Takeaway
When a knowledge base covers multiple domains, tag chunks with metadata and hard-
filter retrieval by it. Semantic similarity alone isn't enough to keep results
on-topic once the corpus is broad — and "return nothing, fall back to generic" is
safer than "search everything" when the right-type content is missing.

---

## 32. Carrying metadata through the pipeline (thread-through)

**Date:** Unknown · *Learned in conversation*

### What is it?
Making a piece of information available deep in the call chain by passing it down
through each function that sits between where it's known and where it's needed.

### Why does it matter?
The report type is worked out early (detection), but it's *needed* late (in
retrieval, several calls away). Retrieval can't filter by a type it doesn't have.
So the type has to be handed down the chain: pipeline → advice generation →
retrieval.

### How does it work?
Add the value as a parameter to each function along the path, defaulting it so the
change is backward-compatible (functions that don't pass it behave as before).
Here: `analyze_report` knows `report_type` → passes it to `generate_advice` →
which passes it to `retrieve_relevant_chunks`. Defaulting `report_type=None` at
each hop meant we could change one function at a time without breaking the others.

### How we use it in this project (HRA-12)
Threaded `report_type` through `pipeline.py` → `advisor.py` → `retriever.py`, one
file at a time, each step safe because of the `None` default.

### A bug this surfaced
Threading the type through made us look at the advisor's "which findings are
abnormal?" test — and it was still checking `status in ("High","Low")`, written
before HRA-06 added *band* statuses like "Prediabetes" and "Borderline High". So
band findings were silently never getting advice. The fix: test the uniform
`severity == "attention"` field (built in HRA-06 for exactly this) instead of the
specific words. A reminder that a uniform signal field pays off precisely when
older code assumed a narrower set of values.

### Takeaway
To use a value far from where it's produced, thread it through the chain as a
defaulted parameter — and change one link at a time. Touching old code on the way
through is also a chance to catch assumptions it baked in before the data grew.

---

## 33. AI-generated domain content and the human-review gate

**Date:** Unknown · *Learned in conversation*

### What is it?
Using an AI to *draft* specialized content (here, medical educational articles),
while treating that draft as provisional until a qualified human reviews it.

### Why does it matter?
An AI can produce fluent, confident-sounding domain text that contains subtle
errors. For low-stakes content that's fine; for content that shapes health
guidance, unreviewed AI prose is risky — it can be wrong while *looking*
authoritative. The safe move isn't "never use AI to draft" or "trust it blindly,"
but "draft with AI, gate on human review."

### How does it work?
- Every drafted article carries an explicit header stating it is AI-drafted and
  pending review — so its status is visible on the face of the content, never
  mistaken for authoritative.
- Content is kept general and educational, never diagnosing, never naming
  medications or dosages (the project's standing safety rules).
- The provisional status is logged as a tracked decision, and a real qualified
  person (here, a doctor) is set to review before it's trusted.

### How we use it in this project (HRA-11)
Rebuilt the knowledge base with ~21 comprehensive articles across five report
types, each with a "pending medical review" header, to be reviewed by a doctor
before being treated as trustworthy. This mirrors the DEC-020 stance on reference
data: illustrative now, authoritative/reviewed as the real bar.

### Takeaway
AI is good at *drafting* specialized content and bad at *guaranteeing* it. Make the
draft status explicit, keep safety framing intact, and put a qualified human review
in the path before the content is trusted — that gate is what makes AI-drafting
responsible rather than reckless.

---

## 34. Mock testing can't catch real-model misbehavior (the JSON-fence lesson)

**Date:** Unknown · *Learned in conversation*

### What is it?
The realization that mock mode — which returns clean, hand-written fake data —
cannot reveal problems that only appear when a *real* model responds in its own
messy way.

### Why does it matter?
The whole pipeline had been tested extensively in mock mode and looked solid. But
the very first time a real PDF hit the real vision model end-to-end, extraction
crashed. Mock data is *perfect* by construction; real model output is not. So an
entire class of bug — "the model didn't format its answer the way we assumed" —
was invisible until a real call was made.

### How does it work? (the specific bug)
The extraction prompt said "respond with ONLY JSON, no code fences." The model
ignored that and wrapped its (otherwise perfect) JSON in a markdown code fence:
```` ```json … ``` ````. So `json.loads` failed at the very first character (a
backtick, not `{`). The fix: parse *tolerantly* — strip a leading/trailing code
fence, and as a fallback slice from the first `{` to the last `}` to ignore any
surrounding prose — then `json.loads`. Still raise on genuinely unparseable output,
so real failures aren't hidden; only *wrapping* is tolerated.

### How we use it in this project
Added an `_extract_json` helper that strips fences/prose before parsing, replacing
the bare `json.loads`. Vision extraction is now resilient to the way real models
actually respond.

### The deeper lesson
Two things: (1) never fully trust a model to obey formatting instructions — parse
its output defensively, because "respond with only JSON" is a request, not a
guarantee. (2) Mock testing proves your *plumbing and structure*, not your
*resilience to real inputs* — so a real end-to-end run is a distinct, necessary
kind of test. Spending the real API call was exactly what caught a bug that would
have crashed on essentially any real report.

### Takeaway
Mock mode validates structure; only real calls validate resilience. Parse model
output defensively (tolerate fences and stray prose), and treat "the first real
run" as its own milestone that will surface things no amount of mock testing could.

---

# Structured output, safety framing, and resilience (learned in conversation)

> From making advice structured (HRA-13), guaranteeing disclaimers (HRA-14),
> grading critical values (HRA-15), and surviving a bad PDF page (HRA-16).

## 35. Structured output from an LLM (and why you parse it defensively)

**Date:** Unknown · *Learned in conversation*

### What is it?
Asking the model to return its answer as *structured data* (JSON with specific
fields) instead of free text, so the program can use each piece separately.

### Why does it matter?
We wanted advice organized per finding (a summary plus one entry per abnormal
marker) so it's cleaner and, later, renderable as separate cards. Free text is one
blob; structured output is data you can loop over.

### How does it work? (and the reliability catch)
You describe the exact JSON shape in the prompt and show an example. But — the
hard-won lesson from the JSON-fence bug — the model doesn't reliably obey. It may
wrap the JSON in code fences, add prose, or mis-name a key. So you *never* trust
the output blindly:
- Parse it through a fence-tolerant helper (shared `extract_json`).
- Have a **fallback**: if parsing fails, degrade gracefully rather than crash —
  we put the model's raw text into the `summary` and return empty structured
  findings, so the advice is *never lost*.
- Choose a shape that's robust to model mistakes: we used a **list** of
  `{name, advice}` rather than a dict keyed by marker name, so a slightly
  mis-named marker can't break the whole structure (a dict key that doesn't match
  would; a list entry just carries the name as a value).

### How we use it in this project (HRA-13)
`generate_advice` returns `{summary, findings:[{name, advice}]}`, prompts for that
shape, parses with `extract_json`, and degrades to summary-only on failure. A real
call confirmed the model produces it well.

### Takeaway
Structured LLM output is powerful but unreliable by nature. Prompt for the shape,
parse defensively, pick a shape tolerant of small model errors, and always have a
degrade-don't-crash fallback.

---

## 36. Guarantee safety-critical things in code, not in the prompt

**Date:** Unknown · *Learned in conversation*

### What is it?
For something that absolutely must be present (a medical disclaimer), don't rely on
the AI to include it — attach it in your own code so it's there every time.

### Why does it matter?
The doctor-consult disclaimer was only appearing because the *model* chose to write
it (we asked it to). But "the model usually complies" is not "always present." On
an off run, or on the degrade-to-summary fallback path, or on the unknown-report
path where the model doesn't run at all, the disclaimer could go missing — and for
a health tool, advice with no "see a doctor" safety net is exactly what you can't
allow.

### How does it work?
Move the guarantee from the prompt (a request) into the code (a certainty). We add
a `disclaimer` field to the result in our own code, on the single exit path, so
*every* result carries it regardless of what the model did. Kept as a separate
field from the model's advice, so it's always rendered in a fixed place and can't
be lost inside generated text.

### How we use it in this project (HRA-14)
`analyze_report` stamps `result["disclaimer"]` on the one return path (covering
numeric, unknown, and narrative branches), sourced from data with a shared default
and per-type override capability. Verified present even on the unknown path where
no advice is generated.

### Takeaway
Anything that *must* be there for safety belongs in code you control, not in an
instruction you hope the model follows. Put invariants on the single exit path so
no branch can skip them.

---

## 37. Grading severity: mild-abnormal vs. critical (and calibrating to avoid false alarms)

**Date:** Unknown · *Learned in conversation*

### What is it?
Distinguishing a *mildly* abnormal value from a *severely* abnormal one, so the
system can respond more urgently to the genuinely alarming case — calmly, without
diagnosing.

### Why does it matter?
Before, "abnormal" was binary: a slightly-low hemoglobin (12.5) and a
dangerously-low one (5.0) were treated identically. A health tool should tell those
apart. But the *opposite* danger is crying wolf — flagging mildly-abnormal values
as "critical" causes needless alarm, which is its own harm.

### How does it work?
- Add optional critical thresholds to the data (e.g. hemoglobin critical-low below
  7). A value past a critical bound gets a third severity, `critical`, above
  `attention`.
- **Calibrate conservatively.** A tempting shortcut — "flag critical if the value
  is X% past the range" — is clinically naive: the same "% over" means totally
  different things for different markers (a mildly-high TSH would wrongly scream
  critical). So thresholds are per-marker, only where reasonably established, and
  set to catch *genuinely* severe values. Many markers get no critical threshold
  and simply never flag critical — the honest "we don't assert this" behavior.
- Keep the messaging calm and non-diagnostic ("significantly outside the typical
  range, generally a reason to seek prompt attention"), and escalate the disclaimer
  rather than alarm.

### How we use it in this project (HRA-15)
`categorize` escalates range markers past `critical_low`/`critical_high`, and bands
via a per-band `critical` severity (glucose split so only >250 is critical, not
every diabetic-range value). Any critical finding swaps in a stronger disclaimer.

### Takeaway
Grade severity so you can respond proportionally — but calibrate carefully, because
false alarms are a real harm too. Prefer per-case thresholds over clever-looking
math, err toward *under*-flagging, and stay silent where you can't justify a claim.

---

## 38. Graceful partial failure (keep the good, report the bad)

**Date:** Unknown · *Learned in conversation*

### What is it?
When processing several pieces and one fails, keep the results from the pieces that
worked, skip the failed one, and tell the user what was skipped — instead of
letting one failure destroy everything.

### Why does it matter?
A multi-page PDF where page 3 is unreadable used to crash the *whole* analysis, so
the user got nothing even though pages 1–2 were perfect. That's wasteful and
frustrating. "All or nothing" is the wrong default when partial success is useful.

### How does it work?
Wrap each piece's processing in its own try/except *inside* the loop. On failure,
catch it, record which piece failed, and continue to the next — rather than letting
the exception propagate out and stop everything. Then surface what was skipped in
the result (not silently), so the user knows the analysis is partial but valid.
Distinguish a genuine *failure* from an *empty-but-fine* piece (a blank page isn't a
failure — it just contributes nothing).

### How we use it in this project (HRA-16)
`_extract_biomarkers_from_pdf` reads each page in its own try/except; a failed page
is skipped and its number collected; the function returns
`(merged_biomarkers, skipped_pages)`, and `analyze_report` surfaces `skipped_pages`
in the result (empty when nothing skipped). The CLI shows a note only when pages
were skipped.

### Takeaway
Where partial results are useful, isolate each unit's failure so one bad unit can't
sink the batch — and report what was skipped rather than dropping it silently.
"Keep the good, report the bad" beats "all or nothing."

---

# Handling messy multi-part input (learned in conversation)

> From HRA-17: making one upload that mixes several report types produce a clean
> per-section result — and the design discipline around it.

## 39. Splitting one input into multiple sections (and the "confident vs. isolated" line)

**Date:** Unknown · *Learned in conversation*

### What is it?
Taking one input that actually contains several different things (a health-checkup
packet with blood + lipid + thyroid results) and splitting it into a section per
thing, instead of forcing it to be a single thing.

### Why does it matter?
The pipeline assumed one report type per upload — it detected the dominant type and
treated everything as that, mishandling markers from the other types. Real reports
are often mixed, so the system needed to handle each type's markers on their own
terms.

### How does it work?
- **Group** each extracted item by which category it belongs to, using data you
  already have (each marker's type is in report_data.json). No new lookup source,
  no AI — just a reverse index.
- **Decide what's a real section vs. noise.** A type with enough markers (a
  threshold) becomes a full, confident section. A type represented by a single
  lone marker does NOT get dressed up as a confident report — because one stray
  marker might be a misread, and a health tool must not manufacture an
  authoritative "you have a lipid problem" section from noise. Lone markers are
  pooled into an honest, low-confidence "isolated" group: still shown (nothing real
  is silently dropped), still categorized, but framed as "these appeared alone, may
  be unreliable, see a doctor."
- **Keep one consistent output shape** whether there's one type or five (always a
  list of sections), so consumers don't branch on "single vs. multi."

### How we use it in this project (HRA-17)
`group_markers_by_type` buckets markers; `analyze_report` builds a full section per
type meeting `SECTION_THRESHOLD`, pools the rest into an "isolated" section, and
returns `{sections:[...], skipped_pages}` for both single- and multi-type reports.

### Takeaway
When one input can contain several things, group by a signal you already have, and
draw a deliberate line between "confident enough to present as its own thing" and
"show it, but honestly flag it as uncertain." Don't manufacture confident output
from thin evidence — but don't silently drop it either.

---

## 40. Challenging a decision from both sides before committing

**Date:** Unknown · *Learned in conversation*

### What is it?
Before locking a design choice, arguing hard *against* it — and against the
alternative too — so the final pick survives real scrutiny rather than being the
first thing that sounded reasonable.

### Why does it matter?
For the "when is a type present enough to be a section?" decision, the first
instinct (a strict threshold) *sounded* robust. But arguing against it surfaced
that it silently drops legitimate lone markers (and several report types naturally
have just one or two markers). Then arguing against the opposite (accept any single
marker) surfaced that it manufactures fake sections from misreads. Only by
pressure-testing *both* did the better answer — a middle path (show lone markers,
but flagged as low-confidence) — become clear.

### How does it work?
For a real design fork, deliberately write the strongest case against each option:
what does it silently lose? what does it wrongly include? where is it weakest, and
is that exactly where it'll be used most? The option still standing after both
critiques — or the synthesis that answers both critiques — is the one to build.

### How we use it in this project
The isolated-section design came directly out of challenging both a strict
threshold and a no-threshold approach, rather than committing to either.

### Takeaway
For consequential decisions, don't just pick and move on — argue both sides to
failure first. The strongest design is often a synthesis that only appears once
you've seen where each pure option breaks.

---

## 41. Removing orphan code (and verifying before you delete)

**Date:** Unknown · *Learned in conversation*

### What is it?
When a change leaves functions with no callers ("orphans"), deleting them — but
checking first that nothing actually still uses them.

### Why does it matter?
The mixed-report rewrite replaced the old single-type routing, leaving three
functions uncalled. Leaving dead code around is a real cost: it confuses future
readers about what's live, and it rots (drifts out of sync with the code that
matters). But deleting blindly risks removing something a *different* module still
imports.

### How does it work?
Search the whole codebase for each name before deleting: `grep -rn "name" .`. If a
name appears only at its own `def`, it's truly orphaned — safe to delete. If it
appears elsewhere (a call, an import), that caller must be handled first. Ignore
matches in compiled caches (.pyc) and in docs describing history. After deleting,
a quick `import` check confirms nothing referenced the removed code.

### How we use it in this project
After HRA-17, grep confirmed `_analyze_numeric`, `_analyze_narrative`, and
`_get_report_category` appeared only at their definitions (plus a stale README
snippet and a historical sprint-board note, both non-code), so all three were
removed and an import check confirmed the tree still loaded.

### A judgment note
One orphan (`_analyze_narrative`) was a deliberate future seam. Deleting it wasn't
losing design — the old stub no longer fit the new sections shape and would need
rewriting for narrative support anyway. The *concept* lives on in the sprint board
and decisions; the obsolete stub didn't need to.

### Takeaway
Delete dead code promptly — but verify it's actually dead first (grep the whole
repo, ignore caches/docs, import-check after). Keeping an obsolete "for later" stub
isn't preserving design when the stub no longer fits where the code has gone.

---

# Contracts, per-person data, and knowing where to stop (learned in conversation)

> From HRA-18 (MCP tool description), HRA-19 (sex-specific ranges), and HRA-21
> (the narrative-handling decision).

## 42. A tool's description is a contract (and it can go stale while the code is fine)

**Date:** Unknown · *Learned in conversation*

### What is it?
When you expose a function as a tool for an AI to call (via MCP), its *description*
(docstring) is what the AI reads to decide when to call it and what it gets back.
That description is a contract — and it can drift out of date even when the code
works perfectly.

### Why does it matter?
Our MCP tool just passes the pipeline's result straight through, so when we changed
the result shape (to the sections structure), the tool kept working — no code
change needed. But its docstring still described the *old* shape. A human reading
code would see "it works." An AI reading the docstring would reason about the wrong
return shape. So "the code is fine" didn't mean "the tool is fine."

### How does it work?
Treat the description as part of what you maintain, not just a comment. When the
behavior or return shape changes, update the description even if the code didn't
change. For AI-facing tools especially, the description is functional — it steers
the caller — not decoration.

### How we use it in this project (HRA-18)
The MCP tool's docstring was rewritten to describe the current sections result
(report type, findings with severity, advice, disclaimer, skipped pages) and the
multi-type/isolated behavior, so the AI host reasons about what it actually
receives. No logic changed — only the contract was brought back in sync.

### Takeaway
A tool's description is a contract with its caller. It can go stale while the code
stays correct — so update descriptions when behavior changes, and especially for
AI-facing tools where the description actively drives how the tool is used.

---

## 43. Personalizing by a per-person attribute (precedence + reading sensitive data)

**Date:** Unknown · *Learned in conversation*

### What is it?
Adjusting results based on a per-person attribute — here, using sex-specific
reference ranges (hemoglobin, hematocrit, RBC differ by sex), so the same value is
judged correctly for that person.

### Why does it matter?
A one-size range mis-judges people: a hemoglobin that's perfectly normal for a woman
can read as "low" against a general range. Personalizing fixes that — but it raises
two real questions: *where does the attribute come from*, and *what if we don't
have it*.

### How does it work?
- **Variant data:** the marker keeps its general range as the default and adds
  per-attribute variants (male/female). The general range is always the safe
  fallback.
- **Source precedence:** the attribute can come from more than one place. We chose:
  the value stated on the document wins, else a value the caller supplied, else fall
  back to the general range. Most-specific-and-trustworthy source first.
- **Never guess the attribute.** Reading sex off a document (via the vision model)
  is less reliable than reading numbers, so we only accept clean, expected values
  and otherwise treat it as unknown — a wrong guess would pick the wrong range,
  which is worse than using the general one. (Sensitive personal data also deserves
  this caution on principle.)

### How we use it in this project (HRA-19)
`variants` blocks on Hb/Hct/RBC; sex read from the report, else caller-supplied,
else general; categorization picks the variant when sex is known. Only
"male"/"female" are accepted; anything else falls back safely.

### Takeaway
To personalize by a per-person attribute: store variants with a safe default,
define a clear source precedence, and never *guess* the attribute — an unknown
value should fall back to the neutral default, not a confident wrong choice.
Especially when the attribute is sensitive or read unreliably.

---

## 44. Deciding where the tool should stop (explain, don't interpret)

**Date:** Unknown · *Learned in conversation*

### What is it?
A design decision about the *limits* of what the tool should do — specifically, that
for word-based (narrative) reports like radiology, the tool will explain the
findings in plain language but will NOT judge whether they're concerning. That
judgment is left to a doctor.

### Why does it matter?
It's tempting to make a tool do *more* — to add a "should I worry?" signal. But for
narrative medical findings, deciding significance from free text *is* clinical
judgment, the exact thing a non-clinician tool should not do, on the highest-stakes
report type. The valuable, safe contribution is explaining what the terms mean —
not re-judging a specialist's findings. So the design win here was deciding *not*
to build the interpretation.

### How does it work?
You draw an explicit line: the tool extracts and explains, but assigns no
status/severity to narrative findings. Significance is deferred to the professional.
This keeps the "rate how bad it is" machinery to numeric markers, where comparing a
number to a range is objective and defensible — and keeps it away from free-text
interpretation, where it isn't.

### How we use it in this project (HRA-21)
Recorded as a decision: narrative findings are explained, not categorized. It's
marked *proposed, pending a medical reviewer's confirmation*, and it gates the
narrative build (HRA-22/23) — we don't build on an unconfirmed safety decision.

### A broader lesson
Knowing where a tool should *stop* is as much a design skill as knowing what to
build. "The tool could do X" isn't the same as "the tool should do X" — especially
when X means making a judgment the tool isn't qualified to make. Choosing not to
build something, and being honest about why, is a legitimate and sometimes the best
design decision.

### Takeaway
Define the limits of what your tool should do, not just its features. For
high-stakes judgments outside the tool's competence, the right move can be to
explain and defer, not to interpret — and to gate building that capability on
expert sign-off.

---

# Refactoring a growing codebase (learned in conversation)

> From the post-first-draft cleanup: splitting overloaded modules, organizing files
> into packages, and renaming the project — all without changing behavior.

## 45. Single-responsibility: splitting modules that grew too many jobs

**Date:** Unknown · *Learned in conversation*

### What is it?
The single-responsibility principle: each module should do one job. Over time, as
features were added story by story, a couple of files quietly took on several jobs —
and this is about splitting them back apart.

### Why does it matter?
`pipeline.py` had become extraction + PDF handling + orchestration + the CLI, and
`detector.py` was detection + grouping + disclaimer lookup. A file doing four
things is harder to read, test, and change — and you can't tell at a glance what
it's responsible for. Splitting restores "one file, one job."

### How does it work?
Identify the distinct jobs a bloated module is doing, and move each into its own
module: extraction → `extractor.py`, disclaimer lookup → `disclaimer.py`, the CLI →
`cli.py`, leaving `pipeline.py` as pure orchestration. The key discipline: it's a
*move*, not a rewrite — behavior must stay identical. Verify with the same output
before and after each move.

### How we use it in this project
Split `pipeline.py` and `detector.py` into focused modules, one move at a time,
smoke-checking identical mock output after each.

### A balance worth noting
Don't over-split. The goal is clear responsibilities, not the maximum number of
tiny files — too many one-function modules is its own readability problem. We kept
detection + grouping together (both "identify the report") rather than splitting
every function out.

### Takeaway
When a module has quietly grown several jobs, split it back to one-job modules — but
as behavior-preserving *moves*, verified each step, and without shredding the code
into confetti.

---

## 46. Python packages & absolute imports (and entry-points-at-root)

**Date:** Unknown · *Learned in conversation*

### What is it?
Organizing modules into sub-folders (packages) and having them import each other by
a full path from the project root (e.g. `from core.categorize import categorize`).

### Why does it matter?
A flat pile of ~16 files is hard to navigate. Grouping them by area (core / rag /
data / utils) makes the structure legible. But folders change how Python imports
work, so it's not just drag-and-drop.

### How does it work?
- A folder becomes an importable **package** by adding an `__init__.py` file to it
  (it can be empty — its presence is what matters).
- With **absolute imports from the root**, every file refers to another by its full
  package path (`core.`, `rag.`, …), and you run from the project root so Python
  resolves them.
- **Entry-point scripts stay at the root.** Scripts you run directly
  (`python3 cli.py`, `build_vector_store.py`, `main.py`) are awkward to run from
  *inside* a package (Python's script-vs-module path handling fights you). Keeping
  the things-you-run at root, and the library code in packages, sidesteps that.

### How we use it in this project
Library modules moved into `core/`, `rag/`, `data/`, `utils/` (each with
`__init__.py`); entry points (`main.py`, `cli.py`, `build_vector_store.py`) stayed
at root; all cross-imports became absolute-from-root.

### Takeaway
Folders need `__init__.py` to be importable; absolute-from-root imports are the
clean convention; and keep the scripts you *run* at the root while the library code
lives in packages — it avoids Python's run-as-script-inside-a-package headache.

---

## 47. Where a file looks for its data (`__file__` vs. working directory)

**Date:** Unknown · *Learned in conversation*

### What is it?
How code finds a data file it needs to open (here, `report_data.json`) — and how
that breaks when you move files into folders.

### Why does it matter?
Several files loaded the JSON via `os.path.dirname(__file__)` — "look next to *me*."
That worked while everything was flat and sat beside the JSON. The moment those
files moved into `core/` but the JSON moved to `data/`, "next to me" pointed at the
wrong folder, and the app couldn't find its data.

### How does it work? (the two approaches)
- **Relative to the file (`__file__`):** "find the data relative to where this
  source file is." Robust to *where you run from*, but fragile when files move
  between folders at different depths (each needs different `../` math).
- **Relative to the working directory:** `os.path.join("data", "report_data.json")`
  — "find it relative to where the program was launched." Simple and identical in
  every file, but it assumes you always run from the project root.

We chose the working-directory approach: one identical line in every loader, which
survives the folder move — at the cost of a "must run from the project root"
requirement (which was already how everything is run).

### How we use it in this project
All four `report_data.json` loaders now use `os.path.join("data", ...)`.

### Takeaway
"Find my data next to my source file" (`__file__`) and "find it relative to where I
was launched" (cwd) are different, and the choice matters when files move. Pick
deliberately, and know the trade-off: cwd-relative is simplest but ties you to
running from a fixed directory.

---

## 48. Grep exhaustively before you edit (don't trust your memory of the code)

**Date:** Unknown · *Learned in conversation*

### What is it?
Before moving or renaming something, searching the *entire* codebase for every
reference to it — rather than relying on memory of "which files use this."

### Why does it matter?
During the refactor, assuming we knew every importer repeatedly missed one: a
fourth file that loaded the JSON (`name_resolver`), a scratch file that imported a
moved module (`playground`), an import line that didn't get updated. Each surfaced
only because a grep (or a crash) found it. Memory of a codebase is unreliable;
search is not.

### How does it work?
For every move/rename, grep the whole repo for the name first:
`grep -rn "the_name" . --include="*.py"`. Treat the grep output — not your memory —
as the authoritative list of what to change. Also: ignore matches in compiled
caches and in docs describing history, and watch for references *inside* functions
(like imports done lazily inside an `if` block), which are easy to forget.

### How we use it in this project
Every step of the split/reorg/rename began with an exhaustive grep for the symbol,
and that's what caught the stragglers a from-memory edit would have missed.

### Takeaway
Before editing across a codebase, let `grep` tell you every place that references
the thing — don't trust your recollection. The references you *forget* are exactly
the ones that break.

---

## 49. Surgical rename: renaming the project without breaking a domain term

**Date:** Unknown · *Learned in conversation*

### What is it?
Renaming the project (blood → health) while a word that *looks* like part of the
name ("blood") is also a legitimate *domain term* that must stay.

### Why does it matter?
"blood" appears everywhere — but in two completely different roles: the *project
name* ("Blood Report Analyser") which we're renaming, and the *report type*
(`"blood"`, `articles/blood/`, blood biomarkers, `MOCK_REPORT=blood`) which is
correct and must NOT change. A blanket find-replace of "blood" would have renamed
the report type and broken the app.

### How does it work?
Rename *surgically*, not with a blanket replace. Grep for the *project-name
patterns* specifically ("blood report", "blood-report", "analyser", the tool name)
— not bare "blood" — then classify each hit as RENAME (project identity) or KEEP
(domain term). Change only the identity references; leave the domain term alone. A
decision log's *historical* entries also stay as-is (you don't rewrite history).

### How we use it in this project
Only four code lines were project-identity (the FastAPI title/status and the MCP
server name + tool name); everything else matching "blood" was the report type or
medical content and was deliberately left untouched.

### Takeaway
A rename is a classification problem, not a find-replace. The same word can be both
the thing you're renaming and a thing you must preserve — so match the specific
*identity* patterns and judge each hit, rather than replacing a bare term blindly.

---

## 50. A virtualenv bakes in its own path (so a folder rename breaks it)

**Date:** Unknown · *Learned in conversation*

### What is it?
A Python virtual environment stores its own absolute location inside its
activation scripts — so if you rename or move the project folder, the venv breaks.

### Why does it matter?
After renaming the project folder, activating the venv failed ("directory does not
exist" pointing at the *old* path). The venv had the old folder path hardcoded
inside it. Nothing wrong with the code — the environment just couldn't follow the
rename.

### How does it work?
A venv isn't portable across a path change; the fix is to recreate it in the new
location (`python3 -m venv venv`, reinstall dependencies). On a restricted machine
where the normal venv tooling is blocked, route around it (create without pip, then
bootstrap pip) — the same "find the permitted path" mindset as other locked-down
workarounds.

### How we use it in this project
Renaming the folder broke the venv; we recreated it in the renamed folder and
reinstalled dependencies to get running again. (A `requirements.txt` would make
that reinstall one command — a tracked follow-up.)

### Takeaway
A virtualenv is tied to its absolute path — moving or renaming the project folder
breaks it, and the fix is to recreate it, not repair it. And this is one more
reason a pinned `requirements.txt` is worth having: rebuilding the environment
should be a single command.

---

*End of current journal. New lessons get appended in this same teaching style as we
learn them.*
