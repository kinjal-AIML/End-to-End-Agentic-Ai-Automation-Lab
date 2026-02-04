"""
Project Structure Generator for BYV Agentic RAG Backend
Run this script to create the complete directory structure
"""

import os
from pathlib import Path


def create_project_structure(base_path="backend"):
    """
    Creates the complete backend directory structure with all files
    """
    
    # Define the structure
    structure = {
        "": [
            ".env",
            "requirements.txt",
            "main.py",
            "ingest.py",
            ".gitignore",
            "README.md"
        ],
        "app": [
            "__init__.py",
            "config.py",
            "schemas.py",
            "prompts.py",
            "state.py"
        ],
        "app/services": [
            "__init__.py",
            "llm.py",
            "vector.py"
        ],
        "app/graph": [
            "__init__.py",
            "nodes.py",
            "edges.py",
            "workflow.py"
        ],
        "data": [
            "raw/",
            "processed/",
            "vectorstore/"
        ]
    }
    
    # File contents templates
    file_contents = {
        ".env": """# API Keys
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Model Configuration
LLM_MODEL=llama-3.3-70b-versatile
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Vector Store
VECTOR_STORE_PATH=./data/vectorstore

# Server Configuration
HOST=0.0.0.0
PORT=8000
""",
        
        "requirements.txt": """# FastAPI
fastapi==0.121.1
uvicorn[standard]==0.35.0
python-multipart==0.0.20
pydantic==2.12.5
pydantic-settings==2.10.1

# LangChain
langchain==1.2.0
langchain-community==0.3.29
langchain-core==1.2.7
langchain-groq==0.3.7
langchain-openai==0.3.32
langgraph==1.0.6

# Vector Store & Embeddings
faiss-cpu==1.12.0
sentence-transformers==2.2.2

# Retrievers
rank-bm25==0.2.2

# Other
python-dotenv==1.1.1
""",
        
        "main.py": """\"\"\"
FastAPI Entry Point
Run with: uvicorn main:app --reload
\"\"\"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.schemas import ChatRequest, ChatResponse
from app.graph.workflow import create_workflow

app = FastAPI(
    title="BYV Agentic RAG API",
    description="Autonomous AI Agent with Hybrid Retrieval",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the workflow
workflow = create_workflow()


@app.get("/")
async def root():
    return {
        "message": "BYV Agentic RAG API",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    \"\"\"
    Main chat endpoint - routes through the LangGraph workflow
    \"\"\"
    try:
        # Run the workflow
        result = workflow.invoke({
            "messages": [request.message],
            "query": request.message,
            "session_id": request.session_id or "default"
        })
        
        return ChatResponse(
            response=result.get("response", ""),
            context=result.get("context", []),
            metadata=result.get("metadata", {})
        )
    except Exception as e:
        return ChatResponse(
            response=f"Error: {str(e)}",
            context=[],
            metadata={"error": True}
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
""",
        
        "ingest.py": """\"\"\"
Data Ingestion Script
Run this manually to build/update the Vector Database

Usage:
    python ingest.py --source data/raw/ --rebuild
\"\"\"

import argparse
from pathlib import Path
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.services.vector import VectorStoreService
from app.config import settings


def load_documents(source_dir: str):
    \"\"\"Load documents from directory\"\"\"
    print(f"📂 Loading documents from: {source_dir}")
    
    loader = DirectoryLoader(
        source_dir,
        glob="**/*.txt",
        loader_cls=TextLoader
    )
    
    documents = loader.load()
    print(f"✅ Loaded {len(documents)} documents")
    return documents


def split_documents(documents):
    \"\"\"Split documents into chunks\"\"\"
    print("🔪 Splitting documents into chunks...")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"✅ Created {len(chunks)} chunks")
    return chunks


def build_vectorstore(chunks, rebuild=False):
    \"\"\"Build or update vector store\"\"\"
    print("🏗️  Building vector store...")
    
    vector_service = VectorStoreService()
    
    if rebuild:
        print("⚠️  Rebuilding from scratch...")
        vector_service.create_vectorstore(chunks)
    else:
        print("📝 Updating existing vectorstore...")
        vector_service.add_documents(chunks)
    
    print("✅ Vector store ready!")


def main():
    parser = argparse.ArgumentParser(description="Ingest documents into vector store")
    parser.add_argument(
        "--source",
        type=str,
        default="data/raw/",
        help="Source directory for documents"
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Rebuild vectorstore from scratch"
    )
    
    args = parser.parse_args()
    
    # Load documents
    documents = load_documents(args.source)
    
    # Split into chunks
    chunks = split_documents(documents)
    
    # Build vectorstore
    build_vectorstore(chunks, rebuild=args.rebuild)
    
    print("\\n🎉 Ingestion complete!")


if __name__ == "__main__":
    main()
""",
        
        ".gitignore": """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
ENV/

# Environment
.env
.env.local

# Vector Store
data/vectorstore/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
""",
        
        "README.md": """# BYV Agentic RAG Backend

Enterprise-grade Autonomous AI Agent with Hybrid Retrieval (BM25 + FAISS)

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Environment
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Ingest Data
```bash
python ingest.py --source data/raw/ --rebuild
```

### 4. Run Server
```bash
python main.py
# or
uvicorn main:app --reload
```

## 📁 Project Structure

```
backend/
├── .env                    # API Keys
├── requirements.txt        # Dependencies
├── main.py                 # FastAPI Entry Point
├── ingest.py               # Vector DB Builder
│
└── app/
    ├── config.py           # Settings
    ├── schemas.py          # Pydantic Models
    ├── prompts.py          # System Prompts
    ├── state.py            # LangGraph State
    │
    ├── services/           # External Integrations
    │   ├── llm.py          # LLM Client
    │   └── vector.py       # Vector Store
    │
    └── graph/              # Agent Logic
        ├── nodes.py        # Agent Functions
        ├── edges.py        # Conditional Logic
        └── workflow.py     # Graph Compilation
```

## 🧪 Testing

```bash
curl -X POST http://localhost:8000/chat \\
  -H "Content-Type: application/json" \\
  -d '{"message": "What technology stack does BYV use?"}'
```

## 📝 License

Proprietary - BYV (Build Your Vision)
""",
        
        "app/__init__.py": """\"\"\"
BYV Agentic RAG Application
\"\"\"

__version__ = "1.0.0"
""",
        
        "app/config.py": """\"\"\"
Application Configuration
All settings, API keys, and constants
\"\"\"

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    \"\"\"Application Settings\"\"\"
    
    # API Keys
    GROQ_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    
    # Model Configuration
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Vector Store
    VECTOR_STORE_PATH: Path = Path("./data/vectorstore")
    
    # Retrieval Configuration
    RETRIEVAL_K: int = 5
    BM25_WEIGHT: float = 0.5
    FAISS_WEIGHT: float = 0.5
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Price Ranges (for lead qualification)
    MIN_PRICE_INFRA: int = 3000
    MAX_PRICE_INFRA: int = 8000
    MIN_PRICE_AI: int = 2500
    MAX_PRICE_AI: int = 15000
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
""",
        
        "app/schemas.py": """\"\"\"
Pydantic Models for API Request/Response
\"\"\"

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ChatRequest(BaseModel):
    \"\"\"Chat request from user\"\"\"
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for context")
    

class ChatResponse(BaseModel):
    \"\"\"Chat response to user\"\"\"
    response: str = Field(..., description="Agent response")
    context: List[str] = Field(default_factory=list, description="Retrieved context")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class Document(BaseModel):
    \"\"\"Document model\"\"\"
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
""",
        
        "app/prompts.py": """\"\"\"
System Prompts for the Agent
Keep all prompts here for easy iteration
\"\"\"

ROUTER_PROMPT = \"\"\"You are a routing agent for BYV (Build Your Vision).

Analyze the user's query and decide:
1. "retrieve" - If the query requires knowledge from the database
2. "direct" - If you can answer directly without retrieval

Examples:
- "What technology stack does BYV use?" → retrieve
- "Hello" → direct
- "Is my data safe?" → retrieve
- "Thank you" → direct

User Query: {query}

Respond with ONLY: retrieve or direct
\"\"\"

GENERATOR_PROMPT = \"\"\"You are BYV's AI Assistant.

Context from knowledge base:
{context}

User Query: {query}

Instructions:
- Answer professionally and accurately
- Use the context provided
- If context doesn't contain the answer, say so politely
- Be concise but informative

Response:
\"\"\"

REFORMULATOR_PROMPT = \"\"\"Reformulate the user's query to improve retrieval.

Original Query: {query}

Make it more specific and search-friendly. Return only the reformulated query.
\"\"\"

LEAD_CAPTURE_PROMPT = \"\"\"The user is interested in our services.

Extract:
- Name (if mentioned)
- Email (if mentioned)
- Company (if mentioned)
- Requirements

From: {query}

Return as JSON.
\"\"\"
""",
        
        "app/state.py": """\"\"\"
LangGraph State Definition
\"\"\"

from typing import TypedDict, List, Optional, Dict, Any


class GraphState(TypedDict):
    \"\"\"State for the agent workflow\"\"\"
    
    # User input
    query: str
    messages: List[str]
    
    # Session
    session_id: str
    
    # Routing
    route: Optional[str]  # "retrieve" or "direct"
    
    # Retrieval
    context: List[str]
    retrieved_docs: List[Dict[str, Any]]
    
    # Generation
    response: str
    
    # Metadata
    metadata: Dict[str, Any]
""",
        
        "app/services/__init__.py": """\"\"\"
External Services Integration
\"\"\"
""",
        
        "app/services/llm.py": """\"\"\"
LLM Service (Groq)
\"\"\"

from langchain_groq import ChatGroq
from app.config import settings


class LLMService:
    \"\"\"LLM Service using Groq\"\"\"
    
    def __init__(self):
        self.llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model_name=settings.LLM_MODEL,
            temperature=0.7
        )
    
    def invoke(self, prompt: str) -> str:
        \"\"\"Invoke the LLM\"\"\"
        response = self.llm.invoke(prompt)
        return response.content


# Global instance
llm_service = LLMService()
""",
        
        "app/services/vector.py": """\"\"\"
Vector Store Service (FAISS + BM25 Hybrid)
\"\"\"

from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from typing import List
from app.config import settings


class VectorStoreService:
    \"\"\"Hybrid Vector Store (FAISS + BM25)\"\"\"
    
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL
        )
        self.vectorstore = None
        self.bm25_retriever = None
        self.load_vectorstore()
    
    def load_vectorstore(self):
        \"\"\"Load existing vectorstore\"\"\"
        try:
            self.vectorstore = FAISS.load_local(
                str(settings.VECTOR_STORE_PATH),
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            print("✅ Vectorstore loaded")
        except:
            print("⚠️  No vectorstore found. Run ingest.py first.")
    
    def create_vectorstore(self, documents: List[Document]):
        \"\"\"Create new vectorstore\"\"\"
        self.vectorstore = FAISS.from_documents(documents, self.embeddings)
        self.vectorstore.save_local(str(settings.VECTOR_STORE_PATH))
        
        # Create BM25 retriever
        self.bm25_retriever = BM25Retriever.from_documents(documents)
        self.bm25_retriever.k = settings.RETRIEVAL_K
    
    def add_documents(self, documents: List[Document]):
        \"\"\"Add documents to existing vectorstore\"\"\"
        if self.vectorstore:
            self.vectorstore.add_documents(documents)
            self.vectorstore.save_local(str(settings.VECTOR_STORE_PATH))
    
    def hybrid_search(self, query: str, k: int = None) -> List[Document]:
        \"\"\"Hybrid search (RRF: BM25 + FAISS)\"\"\"
        k = k or settings.RETRIEVAL_K
        
        if not self.vectorstore or not self.bm25_retriever:
            return []
        
        # Get results from both retrievers
        faiss_docs = self.vectorstore.as_retriever(
            search_kwargs={"k": k * 2}
        ).invoke(query)
        
        bm25_docs = self.bm25_retriever.invoke(query)
        
        # RRF scoring
        doc_scores = {}
        rrf_k = 60
        
        for rank, doc in enumerate(bm25_docs, 1):
            content = doc.page_content
            score = 1 / (rrf_k + rank)
            if content in doc_scores:
                doc_scores[content]['score'] += score * settings.BM25_WEIGHT
            else:
                doc_scores[content] = {'doc': doc, 'score': score * settings.BM25_WEIGHT}
        
        for rank, doc in enumerate(faiss_docs, 1):
            content = doc.page_content
            score = 1 / (rrf_k + rank)
            if content in doc_scores:
                doc_scores[content]['score'] += score * settings.FAISS_WEIGHT
            else:
                doc_scores[content] = {'doc': doc, 'score': score * settings.FAISS_WEIGHT}
        
        # Sort and return top k
        sorted_docs = sorted(doc_scores.values(), key=lambda x: x['score'], reverse=True)
        return [item['doc'] for item in sorted_docs[:k]]


# Global instance
vector_service = VectorStoreService()
""",
        
        "app/graph/__init__.py": """\"\"\"
LangGraph Agent Workflow
\"\"\"
""",
        
        "app/graph/nodes.py": """\"\"\"
Agent Node Functions
Each function represents a node in the workflow
\"\"\"

from app.state import GraphState
from app.services.llm import llm_service
from app.services.vector import vector_service
from app.prompts import ROUTER_PROMPT, GENERATOR_PROMPT


def router_node(state: GraphState) -> GraphState:
    \"\"\"Route the query\"\"\"
    query = state["query"]
    
    # Use LLM to decide
    prompt = ROUTER_PROMPT.format(query=query)
    route = llm_service.invoke(prompt).strip().lower()
    
    state["route"] = route
    state["metadata"] = {"route": route}
    
    return state


def retriever_node(state: GraphState) -> GraphState:
    \"\"\"Retrieve relevant documents\"\"\"
    query = state["query"]
    
    # Hybrid search
    docs = vector_service.hybrid_search(query, k=5)
    
    state["context"] = [doc.page_content for doc in docs]
    state["retrieved_docs"] = [
        {"content": doc.page_content, "metadata": doc.metadata}
        for doc in docs
    ]
    
    return state


def generator_node(state: GraphState) -> GraphState:
    \"\"\"Generate response\"\"\"
    query = state["query"]
    context = "\\n\\n".join(state.get("context", []))
    
    prompt = GENERATOR_PROMPT.format(query=query, context=context)
    response = llm_service.invoke(prompt)
    
    state["response"] = response
    
    return state


def direct_response_node(state: GraphState) -> GraphState:
    \"\"\"Generate direct response without retrieval\"\"\"
    query = state["query"]
    
    # Simple direct responses
    greetings = ["hello", "hi", "hey"]
    thanks = ["thank", "thanks"]
    
    if any(g in query.lower() for g in greetings):
        response = "Hello! I'm BYV's AI assistant. How can I help you today?"
    elif any(t in query.lower() for t in thanks):
        response = "You're welcome! Feel free to ask if you have any other questions."
    else:
        response = llm_service.invoke(f"Respond briefly to: {query}")
    
    state["response"] = response
    
    return state
""",
        
        "app/graph/edges.py": """\"\"\"
Conditional Edge Functions
Determine which node to go to next
\"\"\"

from app.state import GraphState


def should_retrieve(state: GraphState) -> str:
    \"\"\"Decide if we should retrieve or respond directly\"\"\"
    route = state.get("route", "direct")
    
    if route == "retrieve":
        return "retrieve"
    else:
        return "direct"
""",
        
        "app/graph/workflow.py": """\"\"\"
LangGraph Workflow Compilation
This is where the graph is built
\"\"\"

from langgraph.graph import StateGraph, END
from app.state import GraphState
from app.graph.nodes import (
    router_node,
    retriever_node,
    generator_node,
    direct_response_node
)
from app.graph.edges import should_retrieve


def create_workflow():
    \"\"\"Create and compile the workflow\"\"\"
    
    # Initialize graph
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("router", router_node)
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("generator", generator_node)
    workflow.add_node("direct", direct_response_node)
    
    # Set entry point
    workflow.set_entry_point("router")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "router",
        should_retrieve,
        {
            "retrieve": "retriever",
            "direct": "direct"
        }
    )
    
    # Add edges
    workflow.add_edge("retriever", "generator")
    workflow.add_edge("generator", END)
    workflow.add_edge("direct", END)
    
    # Compile
    return workflow.compile()
"""
    }
    
    # Create base directory
    base = Path(base_path)
    base.mkdir(exist_ok=True)
    
    # Create structure
    for folder, files in structure.items():
        # Create folder
        if folder:
            folder_path = base / folder
            folder_path.mkdir(parents=True, exist_ok=True)
        else:
            folder_path = base
        
        # Create files
        for file in files:
            if file.endswith("/"):
                # It's a subdirectory
                (folder_path / file.rstrip("/")).mkdir(exist_ok=True)
            else:
                # It's a file
                file_path = folder_path / file
                
                # Write content if available
                if file in file_contents:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(file_contents[file])
                else:
                    # Create empty file
                    file_path.touch()
    
    print(f"✅ Project structure created at: {base_path}/")
    print("\n📁 Directory tree:")
    print_tree(base)


def print_tree(directory, prefix="", is_last=True):
    """Print directory tree"""
    directory = Path(directory)
    
    # Get all items (excluding __pycache__)
    items = sorted([item for item in directory.iterdir() if item.name != "__pycache__"])
    
    for i, item in enumerate(items):
        is_last_item = i == len(items) - 1
        current_prefix = "└── " if is_last_item else "├── "
        print(f"{prefix}{current_prefix}{item.name}")
        
        if item.is_dir():
            extension = "    " if is_last_item else "│   "
            print_tree(item, prefix + extension, is_last_item)


if __name__ == "__main__":
    import sys
    
    # Get base path from command line or use default
    base_path = sys.argv[1] if len(sys.argv) > 1 else "backend"
    
    create_project_structure(base_path)
    
    print("\n🎉 Done! Next steps:")
    print(f"1. cd {base_path}")
    print("2. pip install -r requirements.txt")
    print("3. Edit .env with your API keys")
    print("4. python ingest.py --source data/raw/ --rebuild")
    print("5. python main.py")