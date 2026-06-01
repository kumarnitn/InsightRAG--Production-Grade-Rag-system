import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from app.database import chroma_client
print("Resetting vector database to clear any stale historical data...")
try:
    chroma_client.reset()
    print("Vector database successfully reset.")
except Exception as e:
    print(f"Database reset warning: {e}")

from app.ingestion import recursive_chunk_text, ingest_document
from app.retrieval import retrieve_relevant_chunks
from app.generation import generate_answer_with_citations
from app.observability import calculate_citation_coverage, get_observability_dashboard_stats, RAGTrace

print("[1] Testing recursive chunking...")
sample_text = (
    "Antigravity AI is an advanced agentic coding system built by the Google DeepMind team. "
    "It runs on specialized container environments and supports direct Pair Programming with users. "
    "The primary objective of Antigravity is to solve complex software engineering tasks with complete "
    "accuracy and high-performance glassmorphic UI dashboards."
)
chunks = recursive_chunk_text(sample_text, chunk_size=150, chunk_overlap=20)
print(f"Chunks generated: {len(chunks)}")
for i, c in enumerate(chunks):
    print(f"  Chunk {i}: {c[:60]}...")
assert len(chunks) >= 2, "Should split into at least 2 chunks"

print("\n[2] Testing document ingestion...")
ingest_res = ingest_document("specs.txt", sample_text)
print("Ingest Result:", ingest_res)
assert ingest_res["status"] == "success", "Ingest should succeed"

print("\n[3] Testing query pipeline execution with RAGTrace monitoring...")
query = "Who built Antigravity?"
with RAGTrace(query=query) as trace:
    # 1. Retrieval
    trace.log_retrieval_start()
    retrieved = retrieve_relevant_chunks(query, top_k=2)
    trace.log_retrieval_end(retrieved_chunks=retrieved)
    print(f"Retrieved {len(retrieved)} chunks:")
    for r in retrieved:
        print(f"  Source: {r['metadata']['source']}, Score: {r['score']}, Snippet: {r['text'][:50]}...")
    assert len(retrieved) > 0, "Should retrieve at least one chunk"
    assert retrieved[0]["metadata"]["source"] == "specs.txt", "Should matchSpecs source"
    
    # 2. Generation
    trace.log_generation_start(context_length=len(retrieved))
    gen_res = generate_answer_with_citations(query, retrieved)
    trace.log_generation_end(result=gen_res)
    print("Answer:", gen_res["answer"])
    print("Citations:", gen_res["citations"])
    assert "answer" in gen_res, "Should contain answer"
    assert len(gen_res["citations"]) > 0, "Should extract at least one citation"
    
    # 3. Post-Process Observability Quality Metric
    coverage = calculate_citation_coverage(gen_res["answer"], gen_res["citations"], retrieved)
    trace.record_final_metrics(result=gen_res, citation_coverage=coverage)
    print(f"Citation Groundedness Coverage: {coverage}%")
    assert 0.0 <= coverage <= 100.0, "Coverage should be a valid percentage"

print("\n[4] Testing observability stats aggregation...")
stats = get_observability_dashboard_stats()
print("Live Stats:", stats)
assert stats["total_requests"] == 1, "Should record 1 request"
assert stats["avg_citation_coverage"] == coverage, "Should match calculated coverage"
assert stats["success_count"] == 1, "Should record 1 successful request"
assert stats["failure_rate"] == 0.0, "Failure rate should be 0.0"

print("\nALL RAG PIPELINE CHECKS PASSED SUCCESSFULLY!")
