import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # LLM Settings (Prefer Google Gemini as default if selected, or OpenAI fallback)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    
    # Langfuse Observability Settings
    LANGFUSE_PUBLIC_KEY: str = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    LANGFUSE_SECRET_KEY: str = os.getenv("LANGFUSE_SECRET_KEY", "")
    LANGFUSE_HOST: str = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    
    # Vector DB settings
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    WEAVIATE_URL: str = os.getenv("WEAVIATE_URL", "")
    WEAVIATE_API_KEY: str = os.getenv("WEAVIATE_API_KEY", "")
    
    # App Settings
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    TOP_K: int = int(os.getenv("TOP_K", "10"))
    
    # Cost per 1k tokens (Fallback/estimated for tracking)
    # Groq Llama3 / Gemini 1.5 Flash input/output estimation
    INPUT_TOKEN_COST_PER_1K: float = 0.00005
    OUTPUT_TOKEN_COST_PER_1K: float = 0.00008

settings = Settings()
