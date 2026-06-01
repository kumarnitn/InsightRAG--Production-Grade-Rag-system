from app.config import settings
from app.database import get_collection

def retrieve_relevant_chunks(query: str, top_k: int = None) -> list[dict]:
    """Retrieves top K relevant chunks for a given query from Chroma."""
    if top_k is None:
        top_k = settings.TOP_K
        
    collection = get_collection()
    
    # Query Chroma
    results = collection.query(
        query_texts=[query],
        n_results=top_k
    )
    
    formatted_chunks = []
    
    if not results or not results['documents'] or len(results['documents'][0]) == 0:
        return formatted_chunks
        
    documents = results['documents'][0]
    metadatas = results['metadatas'][0]
    distances = results['distances'][0] if 'distances' in results and results['distances'] else [0.0] * len(documents)
    ids = results['ids'][0]
    
    for i in range(len(documents)):
        formatted_chunks.append({
            "id": ids[i],
            "text": documents[i],
            "metadata": metadatas[i],
            "distance": distances[i],
            # Normalized score (cosine distance helper, Chroma default L2/cosine depends on setup)
            "score": round(1.0 - distances[i] if distances[i] <= 1.0 else 0.0, 4)
        })
        
    return formatted_chunks
