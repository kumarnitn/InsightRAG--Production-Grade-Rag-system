from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.ingestion import ingest_document
from app.retrieval import retrieve_relevant_chunks
from app.generation import generate_answer_with_citations
from app.observability import RAGTrace, calculate_citation_coverage, get_observability_dashboard_stats, METRICS_STORE
from app.database import chroma_client

app = FastAPI(
    title="Production-Grade RAG Pipeline",
    description="FastAPI backend serving document ingestion, chunking, citation retrieval, and detailed monitoring.",
    version="1.0.0"
)

# Enable CORS for frontend UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str
    top_k: int = 4

@app.post("/api/ingest")
async def ingest_file(file: UploadFile = File(...)):
    """API endpoint to upload and ingest a text-based or PDF document."""
    try:
        content = await file.read()
        
        # Parse PDF documents using pypdf reader instead of raw UTF-8 decode
        if file.filename.lower().endswith('.pdf'):
            import io
            from pypdf import PdfReader
            try:
                pdf_file = io.BytesIO(content)
                reader = PdfReader(pdf_file)
                text_content = ""
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        text_content += text + "\n"
                print(f"Parsed PDF '{file.filename}': extracted {len(text_content)} characters.")
            except Exception as pdf_err:
                raise HTTPException(status_code=400, detail=f"Failed to parse PDF file: {str(pdf_err)}")
        else:
            # Fallback to UTF-8 decoding for TXT/MD/JSON/etc.
            text_content = content.decode("utf-8", errors="ignore")
            
        result = ingest_document(filename=file.filename, file_content=text_content)
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
            
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@app.post("/api/query")
async def run_query(request: QueryRequest):
    """API endpoint to run a user query against the vector index with Langfuse tracing and citations."""
    try:
        # Wrap everything in a RAGTrace context manager to record trace in Langfuse
        with RAGTrace(query=request.query) as trace:
            # 1. Retrieval
            trace.log_retrieval_start()
            chunks = retrieve_relevant_chunks(query=request.query, top_k=request.top_k)
            trace.log_retrieval_end(retrieved_chunks=chunks)
            
            # 2. Generation
            trace.log_generation_start(context_length=len(chunks))
            result = generate_answer_with_citations(query=request.query, retrieved_chunks=chunks)
            trace.log_generation_end(result=result)
            
            # 3. Post-Process Quality Score (Citation Coverage)
            coverage = calculate_citation_coverage(
                answer=result["answer"], 
                citations=result["citations"], 
                retrieved_chunks=chunks
            )
            trace.record_final_metrics(result=result, citation_coverage=coverage)
            
            # Add scores and chunks to the API response
            return {
                "query": request.query,
                "answer": result["answer"],
                "citations": result["citations"],
                "tokens_used": result["tokens_used"],
                "cost": result["cost"],
                "citation_coverage": coverage,
                "retrieved_chunks": chunks
            }
            
    except Exception as e:
        # Locally log uvicorn/fastapi trace and return error
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")

@app.get("/api/observability/stats")
async def get_stats():
    """Endpoint returning live Aggregated Monitoring stats for dashboard."""
    return get_observability_dashboard_stats()

@app.post("/api/observability/reset")
async def reset_pipeline():
    """Helper endpoint to reset metrics and database for evaluation testing."""
    try:
        # Reset memory metrics
        METRICS_STORE["latencies"] = []
        METRICS_STORE["costs"] = []
        METRICS_STORE["citation_coverages"] = []
        METRICS_STORE["failure_counts"] = 0
        METRICS_STORE["success_counts"] = 0
        METRICS_STORE["total_requests"] = 0
        
        # Reset Chroma database
        chroma_client.reset()
        
        return {"status": "success", "message": "Pipeline database and stats reset successful."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Production RAG Backend API!"}
