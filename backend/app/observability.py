import time
import statistics
from langfuse import Langfuse
from app.config import settings

# Initialize Langfuse client
try:
    if settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY:
        langfuse = Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_HOST
        )
        print("Langfuse tracing successfully initialized.")
    else:
        print("WARNING: Langfuse keys missing. Running in dry-run/mock tracing mode.")
        langfuse = None
except Exception as e:
    print(f"Failed to initialize Langfuse client: {e}")
    langfuse = None

# A simple in-memory store to track metrics for real-time dashboard plotting (since Langfuse holds historical data)
# This will allow our custom dashboard UI to plot latency percentiles (P50/P95), cost, and citation coverage immediately!
METRICS_STORE = {
    "latencies": [],
    "costs": [],
    "citation_coverages": [],
    "failure_counts": 0,
    "success_counts": 0,
    "total_requests": 0
}

def get_p50_p95_latencies() -> tuple[float, float]:
    """Calculates P50 and P95 latency percentiles from in-memory metrics store."""
    latencies = METRICS_STORE["latencies"]
    if not latencies:
        return 0.0, 0.0
    sorted_latencies = sorted(latencies)
    n = len(sorted_latencies)
    
    p50_idx = int(n * 0.5)
    p95_idx = int(n * 0.95)
    
    # Boundary correction
    p50_idx = min(p50_idx, n - 1)
    p95_idx = min(p95_idx, n - 1)
    
    return round(sorted_latencies[p50_idx], 3), round(sorted_latencies[p95_idx], 3)

def calculate_citation_coverage(answer: str, citations: list[dict], retrieved_chunks: list[dict]) -> float:
    """
    Measures citation coverage: the percentage of the answer grounded in retrieved evidence.
    Calculates the ratio of sentences with valid citations to the total number of sentences.
    """
    if not answer:
        return 0.0
    
    # Split answer into sentences
    sentences = [s.strip() for s in answer.split('.') if s.strip()]
    if not sentences:
        return 0.0
        
    sentences_with_citation = 0
    for sentence in sentences:
        # Check if sentence contains standard citation pattern, e.g., [1], [2], etc.
        import re
        if re.search(r'\[\d+\]', sentence):
            # Verify the citation is valid and corresponds to an actually retrieved passage
            indices = list(map(int, re.findall(r'\[(\d+)\]', sentence)))
            valid = all(1 <= idx <= len(retrieved_chunks) for idx in indices)
            if valid and indices:
                sentences_with_citation += 1
                
    coverage = (sentences_with_citation / len(sentences)) * 100.0
    return round(coverage, 2)

class RAGTrace:
    """Helper context manager to record trace details in Langfuse & local stats store."""
    def __init__(self, query: str):
        self.query = query
        self.start_time = None
        self.trace = None
        self.retrieval_span = None
        self.generation_span = None
        
    def __enter__(self):
        self.start_time = time.time()
        
        # Create Langfuse Trace
        if langfuse:
            try:
                self.trace = langfuse.trace(
                    name="rag-query-pipeline",
                    user_id="anonymous-user",
                    input={"query": self.query}
                )
            except Exception as e:
                print(f"Error creating Langfuse trace: {e}")
                
        return self
        
    def log_retrieval_start(self):
        """Starts retrieval span logging."""
        if self.trace:
            try:
                self.retrieval_span = self.trace.span(
                    name="semantic-retrieval",
                    input={"query": self.query}
                )
            except Exception as e:
                print(f"Error logging retrieval span: {e}")
                
    def log_retrieval_end(self, retrieved_chunks: list[dict]):
        """Ends retrieval span logging."""
        if self.retrieval_span:
            try:
                self.retrieval_span.end(
                    output={"chunks_retrieved": len(retrieved_chunks), "results": retrieved_chunks}
                )
            except Exception as e:
                print(f"Error ending retrieval span: {e}")
                
    def log_generation_start(self, context_length: int):
        """Starts generation span logging."""
        if self.trace:
            try:
                self.generation_span = self.trace.span(
                    name="answer-generation",
                    input={"context_length": context_length}
                )
            except Exception as e:
                print(f"Error logging generation span: {e}")
                
    def log_generation_end(self, result: dict):
        """Ends generation span logging."""
        if self.generation_span:
            try:
                self.generation_span.end(
                    output={
                        "answer": result["answer"],
                        "citations_count": len(result["citations"]),
                        "tokens_used": result["tokens_used"],
                        "cost": result["cost"]
                    }
                )
            except Exception as e:
                print(f"Error ending generation span: {e}")
                
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        # Update metrics store
        METRICS_STORE["total_requests"] += 1
        
        if exc_type is not None:
            METRICS_STORE["failure_counts"] += 1
            status = "ERROR"
            error_msg = str(exc_val)
        else:
            METRICS_STORE["success_counts"] += 1
            status = "SUCCESS"
            error_msg = None
            
        METRICS_STORE["latencies"].append(duration)
        
        if self.trace:
            try:
                self.trace.end(
                    output={"status": status, "error": error_msg, "duration": duration}
                )
            except Exception as e:
                print(f"Error ending trace: {e}")
                
    def record_final_metrics(self, result: dict, citation_coverage: float):
        """Send custom quality scores back to Langfuse."""
        METRICS_STORE["costs"].append(result["cost"])
        METRICS_STORE["citation_coverages"].append(citation_coverage)
        
        if self.trace:
            try:
                # Log score for citation coverage
                self.trace.score(
                    name="citation-coverage",
                    value=citation_coverage / 100.0,  # normalized 0-1
                    comment="Groundedness of the answer in retrieved context passages"
                )
                # Log score for cost
                self.trace.score(
                    name="request-cost",
                    value=result["cost"],
                    comment="Calculated API cost based on token usage"
                )
            except Exception as e:
                print(f"Error logging scores to Langfuse: {e}")

def get_observability_dashboard_stats() -> dict:
    """Returns aggregated monitoring metrics for the UI dashboard."""
    p50, p95 = get_p50_p95_latencies()
    
    avg_cost = sum(METRICS_STORE["costs"]) / len(METRICS_STORE["costs"]) if METRICS_STORE["costs"] else 0.0
    avg_citation = sum(METRICS_STORE["citation_coverages"]) / len(METRICS_STORE["citation_coverages"]) if METRICS_STORE["citation_coverages"] else 0.0
    
    failure_rate = (METRICS_STORE["failure_counts"] / METRICS_STORE["total_requests"] * 100.0) if METRICS_STORE["total_requests"] > 0 else 0.0
    
    return {
        "p50_latency": round(p50, 3),
        "p95_latency": round(p95, 3),
        "avg_cost": round(avg_cost, 6),
        "avg_citation_coverage": round(avg_citation, 2),
        "failure_rate": round(failure_rate, 2),
        "total_requests": METRICS_STORE["total_requests"],
        "success_count": METRICS_STORE["success_counts"],
        "failure_count": METRICS_STORE["failure_counts"]
    }
