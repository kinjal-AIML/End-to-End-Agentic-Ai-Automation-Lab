import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ... existing keys ...
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Models
    LLM_MODEL = "gpt-4o"
    ROUTER_MODEL = "gpt-4o-mini"
    
    # Vector Paths
    FAISS_INDEX_PATH = "faiss_index_store"
    BM25_INDEX_PATH = "bm25_retriever.pkl"
    HYBRID_SEARCH_K = 4

    # --- EMAIL SETTINGS ---
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD") # The 16-digit App Password
    MAIL_FROM = os.getenv("MAIL_FROM")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_FROM_NAME = "BYV Lead System"
    
    # Where to send the leads? (Your Inbox)
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", os.getenv("MAIL_FROM"))