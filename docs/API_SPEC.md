# API Specification - RAG Platform

This document describes the FastAPI REST API endpoints available for document ingestion, grounded queries, and real-time observability telemetry.

---

## 🚀 Endpoint Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/ingest` | Uploads and processes a document |
| `POST` | `/api/query` | Executes a grounded query with citation maps |
| `GET` | `/api/observability/stats` | Fetches live latency, cost, and citation stats |
| `POST` | `/api/observability/reset` | Resets the vector database and stats store |
| `GET` | `/` | Root health check |

---

## 📥 1. Document Ingestion

### Request
*   **Method**: `POST`
*   **Path**: `/api/ingest`
*   **Content-Type**: `multipart/form-data`
*   **Body Parameters**:
    *   `file`: Binary file upload (supports `.txt`, `.md`, `.json`, `.pdf` up to 10MB)

### Response (`200 OK`)
```json
{
  "status": "success",
  "filename": "deepmind_specs.txt",
  "chunks_count": 4,
  "ingested_at": "2026-05-30T21:00:42.608377"
}
```

---

## 🔍 2. Grounded Query Pipeline

### Request
*   **Method**: `POST`
*   **Path**: `/api/query`
*   **Content-Type**: `application/json`
*   **Body JSON**:
```json
{
  "query": "Who built Antigravity?",
  "top_k": 4
}
```

### Response (`200 OK`)
```json
{
  "query": "Who built Antigravity?",
  "answer": "Based on the documents provided, specifically the source 'specs.txt', the query 'Who built Antigravity?' can be answered as follows: Antigravity AI is an advanced agentic coding system built by the Google DeepMind team... [1].",
  "citations": [
    {
      "citation_index": 1,
      "source": "specs.txt",
      "text": "Antigravity AI is an advanced agentic coding system built by the Google DeepMind team. It runs on specialized container environments...",
      "chunk_index": 0,
      "score": 0.0
    }
  ],
  "tokens_used": 140,
  "cost": 0.000102,
  "citation_coverage": 20.0,
  "retrieved_chunks": [
    {
      "id": "specs.txt_0_8bcfd2",
      "text": "Antigravity AI is an advanced agentic coding system built by the Google DeepMind team. It runs on specialized container environments...",
      "metadata": {
        "source": "specs.txt",
        "chunk_index": 0,
        "total_chunks": 4,
        "ingested_at": "2026-05-30T21:00:42.608377"
      },
      "distance": 0.0,
      "score": 1.0
    }
  ]
}
```

---

## 📊 3. Observability Dashboard Telemetry

### Request
*   **Method**: `GET`
*   **Path**: `/api/observability/stats`

### Response (`200 OK`)
```json
{
  "p50_latency": 0.005,
  "p95_latency": 0.005,
  "avg_cost": 0.000102,
  "avg_citation_coverage": 20.0,
  "failure_rate": 0.0,
  "total_requests": 1,
  "success_count": 1,
  "failure_count": 0
}
```
