# Production Grade RAG system

A production-grade, highly observable Retrieval-Augmented Generation (RAG) system with a glassmorphic dashboard tracking real-time latency (p50/p95), cost-per-request, failure rates, and citation groundedness coverage.

---

## 📂 Repository Layout

```
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py         # Environmental configurations
│   │   ├── database.py       # Chroma client & custom embedding function
│   │   ├── ingestion.py      # Manual recursive chunk splitter
│   │   ├── retrieval.py      # Top-K semantic similarity search
│   │   ├── generation.py     # Prompt engineering & cost estimations
│   │   ├── observability.py  # Langfuse logging & groundedness scores
│   │   └── main.py           # FastAPI REST API endpoints
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── index.html            # Premium dashboard structure
│   ├── style.css             # Glassmorphic glowing stylesheet
│   └── index.js              # State logic & asynchronous request handler
├── tests/
│   ├── verify_rag.py         # PyUnit test suite
│   └── verify_assert.py      # Assertion-based validation suite
└── docs/
    ├── ARCHITECTURE.md       # High-level architecture specification
    ├── API_SPEC.md           # API endpoints & JSON body schemas
    └── ROADMAP.md            # Product roadmap & feature progression
```

---

## ⚡️ Quickstart Guide

### 1. Configure Environmental Keys
Create a `.env` file under `backend/` or export directly:
```bash
GEMINI_API_KEY="your-api-key"
LANGFUSE_PUBLIC_KEY="pk-lf-..."
LANGFUSE_SECRET_KEY="sk-lf-..."
```

### 2. Launch FastAPI Backend Service
Activate the Python virtual environment and run the server using `uvicorn`:
```bash
$ cd rag-project
$ .venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Open UI Client
Open `frontend/index.html` in your web browser. 
*   **Drop zone**: Ingest documents (PDF/TXT/MD/JSON).
*   **Input box**: Ask questions.
*   **Inline references**: Click the highlighted citations `[1]` to review the exact source passage in the popup!
*   **Observability panel**: View real-time aggregated metrics continuously updated with every query execution.

### 4. Run Verification Suite
To verify the entire pipeline end-to-end (ingestion -> chunking -> retrieval -> citation generation -> evaluation metrics):
```bash
$ .venv/bin/python tests/verify_assert.py
```
