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

    # Stage 1
    update("extracting_text", 20)
    time.sleep(13)

    # Stage 2
    update("chunking", 40)
    time.sleep(13)

    # Stage 3
    update("embedding", 70)
    time.sleep(15)

    # Stage 4
    update("storing", 90)
    time.sleep(12)

    # Done
    update("completed", 100)

    return {"message": "Document processed"}