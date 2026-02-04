from langchain_openai import ChatOpenAI
from app.config import Config

# 1. The "Fast" Brain (Routing / Intent)
# Low latency, lower cost.
router_llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0, 
    api_key=Config.OPENAI_API_KEY
)

# 2. The "Smart" Brain (Generation / Sales Logic)
# High reasoning, higher cost.
generator_llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.2, # Slight creativity for natural conversation
    api_key=Config.OPENAI_API_KEY
)

# 3. The Embedding Model (For querying FAISS)
# Must match what you used in ingest.py
from langchain_openai import OpenAIEmbeddings
embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=Config.OPENAI_API_KEY
)