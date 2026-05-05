from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uuid
import asyncio
import json
from fastapi.middleware.cors import CORSMiddleware

from worker import process_document
from redis_client import get_progress, set_progress

app = FastAPI()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UploadRequest(BaseModel):
    text: str


@app.post("/upload")
async def upload(data: UploadRequest):
    doc_id = str(uuid.uuid4())

    set_progress(doc_id, {
        "status": "uploaded",
        "progress": 0
    })

    process_document.delay(doc_id, data.text)

    return {
        "document_id": doc_id
    }


async def event_generator(doc_id: str):
    last_data = None

    while True:
        data = get_progress(doc_id)

        if data != last_data:
            yield f"data: {json.dumps(data)}\n\n"
            last_data = data

        if data and data.get("progress") == 100:
            break

        await asyncio.sleep(1)


@app.get("/stream/{doc_id}")
async def stream(doc_id: str):
    return StreamingResponse(
        event_generator(doc_id),
        media_type="text/event-stream"
    )