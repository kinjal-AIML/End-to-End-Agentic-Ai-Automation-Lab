import uvicorn
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver # Import class here

from src.graph import build_graph
from src.database import get_all_threads, save_thread_title, pool, ensure_custom_tables
from src.rag import ingest_pdf, generate_title, get_current_filename

# Global variables
bot = None
checkpointer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global bot, checkpointer
    
    # 1. Open Pool
    await pool.open()
    
    # 2. Initialize Checkpointer (Now we have a running loop!)
    checkpointer = AsyncPostgresSaver(pool)
    await checkpointer.setup()
    
    # 3. Setup Custom Tables
    await ensure_custom_tables()
    
    # 4. Build Graph (Injecting the ready checkpointer)
    bot = build_graph(checkpointer)
    
    yield
    
    await pool.close()

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

async def stream_generator(user_input: str, thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    final_text = ""
    
    # Use the global 'bot' which is initialized in lifespan
    async for event in bot.astream_events(
        {"messages": [HumanMessage(content=user_input)]}, 
        config, 
        version="v1"
    ):
        kind = event["event"]
        
        if kind == "on_tool_start":
            tool_name = event["name"]
            yield json.dumps({"type": "tool_start", "name": tool_name}) + "\n"

        elif kind == "on_tool_end":
            yield json.dumps({"type": "tool_end", "name": event["name"]}) + "\n"

        elif kind == "on_chat_model_stream":
            chunk = event["data"]["chunk"].content
            if chunk:
                final_text += chunk
                yield json.dumps({"type": "content", "chunk": chunk}) + "\n"

    titles = await get_all_threads()
    exists = any(t['id'] == thread_id for t in titles)
    if not exists and len(user_input) > 0:
        new_title = await generate_title(user_input, final_text)
        await save_thread_title(thread_id, new_title)
        yield json.dumps({"type": "title_update", "title": new_title, "id": thread_id}) + "\n"

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    return StreamingResponse(
        stream_generator(data["message"], data["thread_id"]),
        media_type="application/x-ndjson"
    )

@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...), thread_id: str = Form(...)):
    content = await file.read()
    result = ingest_pdf(content, thread_id, file.filename)
    return result

@app.get("/api/threads")
async def get_threads():
    return await get_all_threads()

@app.get("/api/history/{thread_id}")
async def get_history(thread_id: str):
    # Use global bot
    snapshot = await bot.aget_state({"configurable": {"thread_id": thread_id}})
    messages = []
    if snapshot.values:
        for m in snapshot.values["messages"]:
            msg_type = m.type
            if msg_type in ["human", "ai"]:
                content = m.content
                if msg_type == "ai" and not content: continue
                messages.append({"role": msg_type, "content": content})
    
    current_file = get_current_filename(thread_id)
    return {"messages": messages, "filename": current_file}

@app.get("/")
async def serve_index():
    from fastapi.responses import FileResponse
    return FileResponse("frontend/index.html")

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)