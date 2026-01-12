import uvicorn
import json
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from langchain_core.messages import HumanMessage
from src.graph import build_graph
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Mount the frontend folder to serve static files (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Initialize Graph
bot = build_graph()

async def generate_chat_response(message: str, thread_id: str):
    """
    Generator function that streams tokens from LangGraph to the client.
    """
    input_state = {"messages": [HumanMessage(content=message)]}
    config = {"configurable": {"thread_id": thread_id}}

    # Stream events from the graph
    async for event in bot.astream_events(input_state, config, version="v1"):
        if event["event"] == "on_chat_model_stream":
            chunk = event["data"]["chunk"].content
            if chunk:
                # Yield the text chunk directly
                yield chunk

@app.post("/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    user_message = data.get("message")
    thread_id = data.get("thread_id", "default_user")

    return StreamingResponse(
        generate_chat_response(user_message, thread_id),
        media_type="text/plain"
    )

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)