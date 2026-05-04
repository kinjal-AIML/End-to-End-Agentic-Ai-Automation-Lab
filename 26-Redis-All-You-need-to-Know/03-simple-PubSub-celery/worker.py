from celery_config import celery_app
import time

@celery_app.task(bind=True)
def generate_summary(self, text: str):
    print(f"Processing task: {self.request.id}")
    
    # Simulate AI processing
    time.sleep(15)

    return f"AI Summary: {text[:100]}"