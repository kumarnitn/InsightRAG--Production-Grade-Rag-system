# Product Roadmap - RAG Observability Platform

This document describes the planned progression, optimization phases, and scalability milestones for the Antigravity RAG System.

---

## 📈 Planned Milestones

### Phase 1: Advanced Retrieval Techniques (Q3 2026)
*   **Hybrid Search Integration**: Combine dense vector retrieval with lexical sparse search (BM25) to leverage the advantages of both semantic search and keyword search.
*   **Re-ranking Engine**: Embed a cross-encoder model (e.g., Cohere Rerank or BGE-Reranker) to refine the Top-K retrieved passages, maximizing relevance before generative prompt context assembly.
*   **Context Compression**: Optimize token windows by extracting and passing only the highly relevant context fragments instead of whole raw chunks.

### Phase 2: Observability & Auto-Eval Scaling (Q4 2026)
*   **Continuous Asynchronous Judge**: Deploy an automated LLM-as-a-judge runner using Ragas or TruLens to evaluate 100% of production queries for faithfulness, answer relevance, and context recall, sending scores continuously to Langfuse.
*   **Telemetry Dashboard Upgrades**: Incorporate historical time-series analytics charts in the client UI to track latency, cost, and citation groundedness percentiles over weeks/months.
*   **User Feedback Loop**: Enable users to thumb-up/down generated answers in the frontend, sending manual feedback tags directly into Langfuse trace logging.

### Phase 3: Infrastructure Scaling & Weaviate Migration (Q1 2027)
*   **Weaviate Primary Cluster**: Transition from local ChromaDB to Weaviate cloud/cluster storage to support millions of enterprise documents with sub-second vector queries.
*   **RBAC (Role-Based Access Controls)**: Attach document ACLs (Access Control Lists) to chunk metadata, ensuring that users can only retrieve and generate answers from source documents they are authorized to view.
*   **Embedding/Corpus Drift Monitors**: Detect shifts in query embeddings compared to stored document vector embeddings, alerting administrators when new data updates are required.
