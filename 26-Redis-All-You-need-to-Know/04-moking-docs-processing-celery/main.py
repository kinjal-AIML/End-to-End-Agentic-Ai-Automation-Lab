from fastapi import FastAPI
from pydantic import BaseModel
import uuid

from worker import process_document
from redis_client import get_progress, set_progress

app = FastAPI()


class UploadRequest(BaseModel):
    text: str


@app.post("/upload")
async def upload(data: UploadRequest):
    doc_id = str(uuid.uuid4())

    # initial state
    set_progress(doc_id, {
        "status": "uploaded",
        "progress": 0
    })

    # send to worker
    process_document.delay(doc_id, data.text)

    return {
        "document_id": doc_id,
        "status": "processing"
    }


@app.get("/status/{doc_id}")
async def status(doc_id: str):
    progress = get_progress(doc_id)

    if not progress:
        return {"error": "Document not found"}

    return progress