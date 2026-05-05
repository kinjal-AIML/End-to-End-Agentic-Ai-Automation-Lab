import redis
import json

redis_client = redis.Redis(host="localhost", port=6379, db=2, decode_responses=True)

def set_progress(doc_id, data: dict):
    redis_client.set(f"doc:{doc_id}", json.dumps(data))

def get_progress(doc_id):
    data = redis_client.get(f"doc:{doc_id}")
    return json.loads(data) if data else None