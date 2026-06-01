# Architecture Document

# Production-Grade Enterprise RAG Platform

## 1. Overview

The system is a Production-Grade Retrieval-Augmented Generation (RAG) platform designed to ingest enterprise documents, index them into a vector database, retrieve relevant context for user queries, and generate citation-backed answers.

The architecture prioritizes:

* Scalability
* Reliability
* Observability
* Explainability
* Evaluation
* Cost Control
* Security

---

# 2. High-Level Architecture

```text
                          ┌─────────────────┐
                          │     User        │
                          └────────┬────────┘
                                   │
                                   ▼
                      ┌─────────────────────────┐
                      │ React / NextJS Frontend │
                      └────────┬────────────────┘
                               │
                               ▼
                      ┌─────────────────────────┐
                      │      API Gateway        │
                      └────────┬────────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
         ▼                     ▼                     ▼

┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│ Ingestion      │  │ Retrieval      │  │ Evaluation     │
│ Service        │  │ Service        │  │ Service        │
└───────┬────────┘  └───────┬────────┘  └───────┬────────┘
        │                   │                   │
        ▼                   ▼                   ▼

┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│ Embeddings     │  │ Reranker       │  │ RAGAS          │
│ Service        │  │ Service        │  │ DeepEval       │
└───────┬────────┘  └───────┬────────┘  └────────────────┘
        │                   │
        ▼                   ▼

┌──────────────────────────────────────────────┐
│              Vector Database                 │
│            Qdrant / Weaviate                 │
└──────────────────────────────────────────────┘

                      ▼
          ┌──────────────────────────┐
          │ LLM Generation Service   │
          └───────────┬──────────────┘
                      │
                      ▼
          ┌──────────────────────────┐
          │ Citation Engine          │
          └───────────┬──────────────┘
                      │
                      ▼
          ┌──────────────────────────┐
          │ Final Response           │
          └──────────────────────────┘
```

---

# 3. Core Components

## Frontend

Responsibilities:

* Document Upload
* Query Interface
* Citation Display
* Dashboard
* Evaluation Reports

Technology:

* NextJS
* React
* TailwindCSS

---

## API Gateway

Responsibilities:

* Authentication
* Authorization
* Routing
* Rate Limiting
* Request Validation

Technology:

* FastAPI

Endpoints:

* /upload
* /query
* /documents
* /metrics

---

## Ingestion Service

Responsibilities:

* Document Upload Processing
* Parsing
* Metadata Extraction
* Chunking
* Embedding Generation

Supported Formats:

* PDF
* DOCX
* PPTX
* TXT
* CSV
* Markdown

Libraries:

* PyMuPDF
* pdfplumber
* Unstructured

---

## Embedding Service

Responsibilities:

Convert document chunks into vector representations.

Models:

* text-embedding-3-large
* jina-embeddings-v3
* BGE Embeddings

Input:

Chunk Text

Output:

Embedding Vector

---

## Vector Database

Primary Choice:

Qdrant

Development:

Chroma

Responsibilities:

* Store embeddings
* Similarity search
* Metadata filtering
* Multi-tenant support

Stored Metadata:

```json
{
  "document_id": "doc_123",
  "page": 5,
  "section": "Access Control",
  "source": "security_policy.pdf"
}
```

---

## Retrieval Service

Responsibilities:

* Query Rewriting
* Vector Search
* Hybrid Search
* Context Retrieval

Pipeline:

```text
User Query
    ↓
Query Rewrite
    ↓
Hybrid Search
    ↓
Top 20 Chunks
```

---

## Reranking Service

Responsibilities:

Improve retrieval precision.

Models:

* BGE Reranker
* Cohere Rerank

Pipeline:

```text
Top 20 Chunks
      ↓
Cross Encoder
      ↓
Top 5 Chunks
```

---

## Context Builder

Responsibilities:

Build final prompt context.

Inputs:

* Retrieved Chunks
* Metadata
* Citations

Outputs:

Optimized Context Window

---

## Generation Service

Responsibilities:

* Prompt Construction
* LLM Invocation
* Response Generation

Models:

* GPT-4.1
* Claude Sonnet
* Gemini 2.5 Pro

Prompt Rules:

* Use retrieved context only
* No hallucination
* Provide citations
* Mention uncertainty when evidence is missing

---

## Citation Engine

Responsibilities:

Map generated claims to source chunks.

Output Example:

```text
Remote work is allowed three days per week [1].

References

[1] employee_handbook.pdf Page 12
```

---

## Evaluation Service

Responsibilities:

Measure RAG quality.

Frameworks:

* RAGAS
* DeepEval
* Langfuse Evaluations

Metrics:

* Faithfulness
* Answer Relevance
* Context Precision
* Context Recall
* Citation Coverage

---

# 4. Retrieval Architecture

## Hybrid Search

The platform uses:

```text
BM25
+
Vector Search
```

Advantages:

* Semantic Understanding
* Exact Keyword Matching
* Better Recall
* Better Precision

---

## Retrieval Pipeline

```text
User Query
      ↓
Query Rewriting
      ↓
Hybrid Search
      ↓
Top 20 Chunks
      ↓
Reranking
      ↓
Top 5 Chunks
      ↓
Context Builder
      ↓
LLM
```

---

# 5. Data Flow

## Document Ingestion

```text
Upload
   ↓
Validation
   ↓
Parsing
   ↓
Metadata Extraction
   ↓
Chunking
   ↓
Embedding
   ↓
Vector Storage
```

---

## User Query

```text
Question
    ↓
Embedding
    ↓
Vector Search
    ↓
Reranking
    ↓
Context Building
    ↓
LLM
    ↓
Citation Engine
    ↓
Answer
```

---

# 6. Chunking Strategy

The system uses semantic chunking.

Avoid:

* Fixed Character Splits

Prefer:

* Heading-Based Splits
* Section-Based Splits
* Semantic Splits

Metadata Stored:

```json
{
  "chunk_id": "chunk_45",
  "page": 12,
  "section": "Access Control"
}
```

---

# 7. Storage Architecture

## Object Storage

Purpose:

Store original documents.

Options:

* AWS S3
* MinIO

---

## PostgreSQL

Stores:

* Users
* Documents
* Metadata
* Queries
* Evaluation Results
* Feedback

Tables:

```text
users
documents
chunks
queries
feedback
evaluations
audit_logs
```

---

## Vector Database

Stores:

* Embeddings
* Chunk Metadata

Collection:

```text
documents
```

---

# 8. Observability Architecture

## Langfuse

Every request must generate a trace.

Trace Flow:

```text
User Query
     ↓
Retriever
     ↓
Reranker
     ↓
Prompt Builder
     ↓
LLM
     ↓
Response
```

Tracked:

* Tokens
* Cost
* Latency
* Retrieval Results
* Prompt Versions

---

## OpenTelemetry

Instrument:

* API Gateway
* Retrieval Service
* Generation Service
* Evaluation Service

Generate:

* Distributed Traces
* Request IDs
* Service Metrics

---

## Prometheus

Collect:

* CPU Usage
* Memory Usage
* Request Counts
* Error Rates

---

## Grafana

Dashboards:

* Latency Dashboard
* Cost Dashboard
* Quality Dashboard
* Infrastructure Dashboard

---

# 9. Evaluation Architecture

Evaluation runs continuously.

Metrics:

## Retrieval Metrics

* Context Precision
* Context Recall
* MRR
* NDCG

## Generation Metrics

* Faithfulness
* Answer Relevance
* Hallucination Rate

## Citation Metrics

* Citation Coverage
* Citation Accuracy

---

# 10. Regression Gates

Every deployment must pass:

```text
Faithfulness > 0.90

Citation Coverage > 0.95

P95 Latency < 5 sec

Hallucination Rate < 1%
```

Failure results in deployment rejection.

---

# 11. Security Architecture

Authentication:

* JWT

Authorization:

* RBAC

Roles:

* Admin
* Editor
* Viewer

Security Controls:

* HTTPS
* Encryption at Rest
* Encryption in Transit
* Audit Logging
* Tenant Isolation

---

# 12. Deployment Architecture

Containerized Services:

* frontend
* gateway
* ingestion-service
* retrieval-service
* generation-service
* evaluation-service
* postgres
* qdrant
* langfuse

Deployment:

```text
Docker
      ↓
Kubernetes
      ↓
Production Cluster
```

Infrastructure:

* AWS
* Azure
* GCP

---

# 13. Future Enhancements

## Multi-Agent Architecture

Agents:

* Query Understanding Agent
* Retrieval Agent
* Verification Agent
* Research Agent
* Report Generation Agent

Using LangGraph.

---

## Advanced Retrieval

* Multi Query Retrieval
* Parent Child Retrieval
* Graph RAG
* Knowledge Graph Integration

---

## Human Feedback Loop

Collect:

* Ratings
* Corrections
* User Validation

Feed back into evaluation pipeline.

---

# 14. Architectural Principles

1. Retrieval First, Generation Second
2. Every Answer Must Be Grounded
3. Every Claim Must Be Traceable
4. Everything Must Be Observable
5. Quality Must Be Measured Continuously
6. Deployments Must Be Evaluation-Gated
7. Services Must Be Independently Scalable
8. Security Must Be Built-In
9. Cost Must Be Measured Per Request
10. Production Reliability Over Demo Simplicity
