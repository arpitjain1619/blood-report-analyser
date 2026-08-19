# Blood Report Analyser

An AI-powered pipeline that reads a blood test report image, extracts biomarker
values using a vision-capable LLM, categorizes each value against reference
ranges, and generates personalized, non-diagnostic health guidance grounded in
a curated knowledge base using Retrieval-Augmented Generation (RAG).

Built as a hands-on learning project to understand real AI engineering
concepts — vision LLMs, structured output, embeddings, semantic search, and
RAG — including production-minded concerns like rate-limit resilience and
model fallback.

> ⚠️ **Educational project only.** Not a medical device, and not a substitute
> for professional medical advice. All generated guidance is general and
> non-diagnostic, and always recommends consulting a licensed doctor.

## Current Status

🟡 **Work in progress.** Currently a command-line pipeline — not yet wrapped
as an API/service. See [Roadmap](#roadmap) below.

## How It Works

1. **Vision extraction** — a vision-capable LLM reads the report image and
   extracts biomarker name/value pairs as structured JSON.
2. **Categorization** — each value is compared against a reference range
   chart (plain Python, no AI call — this is a deterministic comparison) and
   tagged High / Low / Normal.
3. **Retrieval (RAG)** — for each abnormal biomarker, the system embeds a
   query and searches a knowledge base of biomarker-guidance articles using
   cosine similarity to find the most relevant context.
4. **Generation** — the LLM writes personalized, general guidance, grounded
   only in the retrieved context, with a mandatory doctor-consultation
   disclaimer.

## Tech Stack

- **Language:** Python
- **LLM provider:** [OpenRouter](https://openrouter.ai) (free-tier models),
  accessed via the OpenAI-compatible SDK
- **Vector store:** In-memory / local JSON file (`vector_store.json`) — kept
  simple deliberately, to learn the underlying mechanics before reaching for
  a dedicated vector database
- **Vision model:** `google/gemma-4-31b-it:free` (with fallback models)
- **Embedding model:** `nvidia/llama-nemotron-embed-vl-1b-v2:free`

## Project Structure

```
blood-report-analyser/
├── articles/                  # RAG knowledge base (14 biomarker guidance articles)
├── reference_ranges.py        # Biomarker normal-range reference chart
├── categorize.py              # Rule-based High/Low/Normal categorization
├── load_articles.py           # Loads knowledge base articles from disk
├── chunker.py                 # Splits article text into overlapping chunks
├── embedder.py                # Converts text into embeddings
├── build_vector_store.py      # One-time script: chunks + embeds all articles
├── retriever.py                # Semantic search via cosine similarity
├── advisor.py                  # Generates grounded advice using RAG
├── pipeline.py                 # Full pipeline entry point (image → advice)
├── playground.py               # Scratch file for testing/exploring concepts
├── sample_report.png           # Synthetic mock report for testing
└── vector_store.json           # Generated embeddings (not committed to git)
```

## Setup

```bash
# Clone the repo
git clone https://github.com/arpitjain1619/blood-report-analyser.git
cd blood-report-analyser

# Create and activate a virtual environment
python3 -m venv venv        # or: python3 -m virtualenv venv
source venv/bin/activate

# Install dependencies
pip install openai python-dotenv numpy pillow

# Add your OpenRouter API key
echo "OPENROUTER_API_KEY=your-key-here" > .env
```

## Usage

```bash
# One-time: build the vector store from the knowledge base
python3 build_vector_store.py

# Run the full pipeline on a sample report
python3 pipeline.py
```

## Roadmap

- [x] Vision-based biomarker extraction
- [x] Rule-based categorization
- [x] RAG knowledge base (chunking, embeddings, retrieval, generation)
- [x] Rate-limit resilience (retry + multi-model fallback)
- [ ] Wrap as a FastAPI service
- [ ] Proper automated tests (currently informal, scratch-based testing only)
- [ ] Logging, evaluation, and further production-readiness work

## Disclaimer

This project generates general, educational health information only. It does
not diagnose conditions, recommend medications or dosages, and is not a
substitute for professional medical advice. Always consult a licensed doctor
to interpret real blood test results.
