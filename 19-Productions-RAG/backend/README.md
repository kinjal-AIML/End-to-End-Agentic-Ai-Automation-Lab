# BYV Agentic RAG Backend

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
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What technology stack does BYV use?"}'
```

## 📝 License

Proprietary - BYV (Build Your Vision)
