from celery_config import celery_app
from redis_client import set_progress
import time

@celery_app.task(bind=True)
def process_document(self, doc_id: str, text: str):

    def update(status, progress):
        set_progress(doc_id, {
            "status": status,
            "progress": progress
        })

    update("extracting_text", 20)
    time.sleep(3)

    update("chunking", 40)
    time.sleep(3)

    update("embedding", 70)
    time.sleep(5)

    update("storing", 90)
    time.sleep(2)

    update("completed", 100)

    return {"message": "done"}