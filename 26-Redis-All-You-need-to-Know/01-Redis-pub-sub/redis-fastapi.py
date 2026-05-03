from fastapi import FastAPI, HTTPException
import redis.asyncio as redis
import httpx
import json

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    app.state.redis = redis.Redis(host='localhost', port=6379, db=0)
    app.state.http_client = httpx.AsyncClient()


@app.on_event("shutdown")
async def shutdown_event():
    await app.state.redis.close()
    await app.state.http_client.aclose()


@app.get("/entries")
async def read_item():
    try:
        # 1. Check Redis
        cached = await app.state.redis.get("entries")

        if cached:
            return json.loads(cached)

        # 2. Fetch API
        response = await app.state.http_client.get(
            "https://jsonplaceholder.typicode.com/posts"
        )
        response.raise_for_status()
        data = response.json()

        # 3. Store in Redis
        await app.state.redis.set("entries", json.dumps(data), ex=60)

        return data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))