import os
import httpx
import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb import EmbeddingFunction, Documents, Embeddings
from app.config import settings

# Dynamic defensive import for Google Gemini SDK
gemini_enabled = False
if settings.GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        gemini_enabled = True
    except ImportError:
        print("WARNING: google-generativeai package not installed. Gemini embeddings disabled.")

class GeminiEmbeddingFunction(EmbeddingFunction):
    """Custom embedding function using Google Gemini API."""
    def __call__(self, input: Documents) -> Embeddings:
        try:
            import google.generativeai as genai
            response = genai.embed_content(
                model="models/embedding-001",
                content=input,
                task_type="retrieval_document"
            )
            return response['embedding']
        except Exception as e:
            print(f"Error generating Gemini embeddings: {e}")
            raise e

class BGEHuggingFaceEmbeddingFunction(EmbeddingFunction):
    """Custom embedding function querying HuggingFace Inference API for BAAI/bge-large-en-v1.5."""
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("HF_API_KEY", "")
        self.url = "https://api-inference.huggingface.co/pipeline/feature-extraction/BAAI/bge-large-en-v1.5"

    def __call__(self, input: Documents) -> Embeddings:
        try:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
                
            payload = {"inputs": input, "options": {"wait_for_model": True}}
            
            with httpx.Client(timeout=20.0) as client:
                response = client.post(self.url, headers=headers, json=payload)
                if response.status_code == 200:
                    embeddings = response.json()
                    if isinstance(embeddings, list) and len(embeddings) > 0:
                        return embeddings
                else:
                    print(f"HuggingFace Inference API Error ({response.status_code}): {response.text}")
        except Exception as e:
            print(f"Error querying HuggingFace BGE Inference API: {e}")
            
        raise RuntimeError("Failed to generate BGE embeddings from HuggingFace Inference API.")

# Select Embedding Function based on user request (BAAI/bge-large-en-v1.5)
embedding_function = None

# 1. Attempt BAAI/bge-large-en-v1.5 local loading
try:
    from chromadb.utils import embedding_functions
    print("Attempting to initialize BAAI/bge-large-en-v1.5 local sentence-transformers model...")
    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="BAAI/bge-large-en-v1.5"
    )
    print("SUCCESS: Loaded local BAAI/bge-large-en-v1.5 model.")
except Exception as local_err:
    print(f"Note: Local sentence-transformers package not configured or model load failed: {local_err}")
    
    # 2. Fall back to HuggingFace Inference API for BAAI/bge-large-en-v1.5
    print("Falling back to HuggingFace Inference API for BAAI/bge-large-en-v1.5 embeddings...")
    embedding_function = BGEHuggingFaceEmbeddingFunction()
    try:
        # Verify connection and model availability with a quick mock call
        test_embed = embedding_function(["test connection"])
        print("SUCCESS: Configured BAAI/bge-large-en-v1.5 HuggingFace API embeddings.")
    except Exception as api_err:
        print(f"ERROR: HuggingFace BGE Inference API test failed: {api_err}")
        print("Falling back to ChromaDB's default local ONNX MiniLM model to keep the system working.")
        embedding_function = None

# Initialize ChromaDB client
try:
    os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
    chroma_client = chromadb.PersistentClient(
        path=settings.CHROMA_PERSIST_DIR,
        settings=ChromaSettings(allow_reset=True, anonymized_telemetry=False)
    )
except Exception as e:
    print(f"Error initializing ChromaDB client: {e}")
    chroma_client = chromadb.EphemeralClient()

def get_collection(name: str = "rag_documents"):
    """Get or create a ChromaDB collection with robust embeddings."""
    if embedding_function is None:
        return chroma_client.get_or_create_collection(
            name=name
        )
    return chroma_client.get_or_create_collection(
        name=name,
        embedding_function=embedding_function
    )
