"""
FastAPI Entry Point
Run with: uvicorn main:app --reload
"""

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
    """
    Main chat endpoint - routes through the LangGraph workflow
    """
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
