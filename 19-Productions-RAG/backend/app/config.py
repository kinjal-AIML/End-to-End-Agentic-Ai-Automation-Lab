import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Keys
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Models
    LLM_MODEL = "gpt-4o" # The "Smart" model for generation
    ROUTER_MODEL = "gpt-4o-mini" # The "Fast" model for routing
    
    # Paths (Relative to the backend root)
    FAISS_INDEX_PATH = "faiss_index_store"
    BM25_INDEX_PATH = "bm25_retriever.pkl"
    
    # Thresholds
    HYBRID_SEARCH_K = 4 # Number of docs to retrieve