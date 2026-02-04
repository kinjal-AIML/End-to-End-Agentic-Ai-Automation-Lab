from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import uvicorn

from app.schemas import ChatRequest
from app.graph.workflow import app_graph
from langchain_core.messages import HumanMessage

app = FastAPI(title="BYV Architect API", version="1.0.0")

# CORS Middleware (Crucial for allowing requests from your Next.js Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, change this to your Vercel domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def health_check():
    return {"status": "ok", "service": "BYV Architect Agent"}

# @app.post("/chat/stream")
# async def stream_chat(request: ChatRequest):
#     """
#     Main Endpoint. Receives User Message + URL.
#     Streams the output token-by-token.
#     """
    
#     # 1. Prepare Input State
#     input_state = {
#         "messages": [HumanMessage(content=request.message)],
#         "current_url": request.url,
#         "session_id": request.session_id,
#         "user_email": request.user_email
#     }

#     # 2. Generator Function for Streaming
#     # We use LangGraph's .stream() method to get updates in real-time
#     async def event_generator():
#         try:
#             # 'stream_mode="updates"' gives us the output of each node as it finishes
#             # But for the final LLM text, we want to capture the generator's token stream.
#             # However, for simplicity and robustness in this version, we will stream the 
#             # Final Message chunks.
            
#             # NOTE: If you want token-by-token streaming from the LLM within the graph, 
#             # you need to use .astream_events(). Here is the implementation:
            
#             async for event in app_graph.astream_events(input_state, version="v1"):
                
#                 # Capture Generator Tokens (The "Talking" part)
#                 if event["event"] == "on_chat_model_stream":
#                     # We check if this stream is coming from the 'generate' node
#                     # (To avoid streaming the router's internal thoughts)
#                     if event["metadata"].get("langgraph_node") == "generate":
#                         chunk = event["data"]["chunk"].content
#                         if chunk:
#                             # Send SSE (Server-Sent Event) format
#                             yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"

#                 # Capture Logic Events (Optional: Tell frontend what we are doing)
#                 elif event["event"] == "on_chain_start":
#                     if event["name"] == "retrieve":
#                         yield f"data: {json.dumps({'type': 'status', 'content': 'Reading Documents...'})}\n\n"
#                     elif event["name"] == "router":
#                         yield f"data: {json.dumps({'type': 'status', 'content': 'Analyzing Request...'})}\n\n"

#             # End of Stream
#             yield "data: [DONE]\n\n"

#         except Exception as e:
#             error_msg = json.dumps({"error": str(e)})
#             yield f"data: {error_msg}\n\n"

#     # 3. Return Streaming Response
#     return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/chat/stream")
async def stream_chat(request: ChatRequest):
    
    # 1. Config with Thread ID (This is the "Memory Key")
    config = {"configurable": {"thread_id": request.session_id}}

    # 2. Prepare Input 
    # NOTE: We only pass the NEW message. LangGraph pulls the old ones from Memory.
    input_state = {
        "messages": [HumanMessage(content=request.message)],
        "current_url": request.url,
        "user_email": request.user_email
    }

    async def event_generator():
        try:
            # Pass 'config' to astream_events
            async for event in app_graph.astream_events(input_state, config=config, version="v1"):
                
                if event["event"] == "on_chat_model_stream":
                    if event["metadata"].get("langgraph_node") == "generate":
                        chunk = event["data"]["chunk"].content
                        if chunk:
                            yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"

                elif event["event"] == "on_chain_start":
                    # if event["name"] == "retrieve":
                    #     yield f"data: {json.dumps({'type': 'status', 'content': 'Reading Documents...'})}\n\n"
                    # RETRIEVER STATUS
                    if event["name"] == "retrieve":
                        yield f"data: {json.dumps({'type': 'status', 'content': 'Reading Document...'})}\n\n"
                    
                    # ROUTER STATUS
                    elif event["name"] == "router":
                        yield f"data: {json.dumps({'type': 'status', 'content': 'Analyzing Intent...'})}\n\n"
                    
                    # NEW: LEAD CAPTURE STATUS
                    elif event["name"] == "capture":
                        # We only want to show this if we are actually processing something
                        yield f"data: {json.dumps({'type': 'status', 'content': 'Checking details...'})}\n\n"

            yield "data: [DONE]\n\n"

        except Exception as e:
            error_msg = json.dumps({"error": str(e)})
            yield f"data: {error_msg}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    print("🚀 Starting BYV Architect Server...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)