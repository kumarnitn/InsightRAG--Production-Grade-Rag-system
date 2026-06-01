import uuid
import datetime
from app.config import settings
from app.database import get_collection

def recursive_chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    """Manually splits text recursively by double newline, single newline, spaces to keep semantic chunks."""
    if not text:
        return []
        
    chunks = []
    start = 0
    while start < len(text):
        # If remaining text is smaller than chunk_size, grab the rest and finish to prevent infinite loops
        if start + chunk_size >= len(text):
            chunk = text[start:].strip()
            if chunk:
                chunks.append(chunk)
            break
            
        end = start + chunk_size
        
        # Try to find a logical boundary (like a paragraph or sentence end) near the end of the window
        boundary = text.rfind("\n\n", start, end)
        if boundary == -1 or boundary < start + (chunk_size // 2):
            # Try single newline
            boundary = text.rfind("\n", start, end)
        if boundary == -1 or boundary < start + (chunk_size // 2):
            # Try period with space (sentence boundary)
            boundary = text.rfind(". ", start, end)
        if boundary == -1 or boundary < start + (chunk_size // 2):
            # Try space
            boundary = text.rfind(" ", start, end)
            
        if boundary != -1 and boundary > start:
            end = boundary + 1  # include space or punctuation
            
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
            
        # Ensure we strictly advance
        next_start = end - chunk_overlap
        if next_start <= start:
            next_start = start + (chunk_size // 2)
        start = next_start
        
    return chunks

def ingest_document(filename: str, file_content: str) -> dict:
    """Ingests a document into the Chroma collection by chunking and embedding it."""
    # Chunking
    chunks = recursive_chunk_text(
        text=file_content, 
        chunk_size=settings.CHUNK_SIZE, 
        chunk_overlap=settings.CHUNK_OVERLAP
    )
    
    if not chunks:
        return {"status": "error", "message": "No text content found to ingest."}
        
    # Get vector collection
    collection = get_collection()
    
    # Prepare data for Chroma
    ids = []
    documents = []
    metadatas = []
    
    timestamp = datetime.datetime.now().isoformat()
    
    for i, chunk in enumerate(chunks):
        chunk_id = f"{filename}_{i}_{str(uuid.uuid4())[:8]}"
        ids.append(chunk_id)
        documents.append(chunk)
        metadatas.append({
            "source": filename,
            "chunk_index": i,
            "total_chunks": len(chunks),
            "ingested_at": timestamp
        })
        
    # Add to Chroma collection (which implicitly calls embedding function)
    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )
    
    return {
        "status": "success",
        "filename": filename,
        "chunks_count": len(chunks),
        "ingested_at": timestamp
    }
