<div align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/RAG-Production_Grade-FF6B6B?style=for-the-badge" alt="RAG" />
  <img src="https://img.shields.io/badge/ChromaDB-Data-blue?style=for-the-badge" alt="ChromaDB" />
</div>

<h1 align="center">Production Grade RAG System 🚀</h1>

<p align="center">
  <b>A high-performance, observable Retrieval-Augmented Generation (RAG) system with a premium glassmorphic dashboard.</b><br>
  <i>Track real-time latency (p50/p95), cost-per-request, failure rates, and citation groundedness seamlessly.</i>
</p>

---

## ✨ Features

- **End-to-End RAG Pipeline**: Robust ingestion, chunking, and semantic retrieval.
- **Real-Time Observability**: Built-in tracking for API latency, LLM cost estimation, and query success rates.
- **Citation Grounding**: Every answer provides precise, clickable citations mapped directly to source documents.
- **Premium UI/UX**: Stunning glassmorphic frontend built for an immersive user experience.
- **Extensive Testing**: Comprehensive PyUnit and assertion-based validation suites.

## 🛠️ Technology Stack

- **Backend**: FastAPI, Python
- **Database**: ChromaDB (Vector Store)
- **Frontend**: Vanilla HTML/CSS/JS (Glassmorphic Design)
- **Observability**: Langfuse Logging & Groundedness Metrics
- **Testing**: PyUnit

## 📂 Project Structure

```text
├── backend/
│   ├── app/
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

## 🚀 Quickstart Guide

### 1. Configure Environment Variables
Create a `.env` file under the `backend/` directory and add your API keys:

```bash
GEMINI_API_KEY="your-gemini-api-key"
LANGFUSE_PUBLIC_KEY="pk-lf-..."
LANGFUSE_SECRET_KEY="sk-lf-..."
```

### 2. Launch Backend Service
Activate your Python virtual environment and start the FastAPI server:

```bash
cd rag-project
.venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Open the UI Client
Simply open `frontend/index.html` in your web browser. 
- **Drop Zone**: Upload and ingest your documents (`.pdf`, `.txt`, `.md`, `.json`).
- **Query Box**: Ask context-aware questions.
- **Inline References**: Click on highlighted citations (e.g., `[1]`) to review the exact source passages in a popup.
- **Observability Panel**: Monitor real-time aggregated metrics continuously updated with every query execution.

### 4. Run Verification Suite
Validate the entire pipeline end-to-end (ingestion → chunking → retrieval → citation generation → evaluation metrics) with a single command:

```bash
.venv/bin/python tests/verify_assert.py
```

## 📈 Roadmap & Architecture
For deep-dives into the system's design and upcoming features, check the `/docs` directory:
- [System Architecture](docs/ARCHITECTURE.md)
- [API Specifications](docs/API_SPEC.md)
- [Future Roadmap](docs/ROADMAP.md)

---
<p align="center"><i>Crafted for high performance and reliability.</i></p>
