from fastapi import FastAPI
from pydantic import BaseModel
from celery.result import AsyncResult

from worker import generate_summary
from celery_config import celery_app

app = FastAPI()

class RequestData(BaseModel):
    text: str


@app.post("/generate")
async def generate(data: RequestData):
    task = generate_summary.delay(data.text)

    return {
        "task_id": task.id,
        "status": "processing"
    }


@app.get("/status/{task_id}")
async def get_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)

    response = {
        "task_id": task_id,
        "status": task_result.status
    }

    if task_result.status == "SUCCESS":
        response["result"] = task_result.result

    return response