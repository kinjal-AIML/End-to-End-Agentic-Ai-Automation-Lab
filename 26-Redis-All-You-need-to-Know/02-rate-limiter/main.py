from fastapi import FastAPI, HTTPException, Request
import redis.asyncio as redis
import httpx
import json
from rate_limiting import rate_limiter

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    app.state.redis = redis.Redis(host='localhost', port=6379, db=0)
    app.state.http_client = httpx.AsyncClient()


@app.on_event("shutdown")
async def shutdown_event():
    await app.state.redis.close()
    await app.state.http_client.aclose()


from fastapi import Depends

@app.get("/entries")
async def read_item(
    request: Request,
    _: None = Depends(rate_limiter)  # 👈 rate limit applied here
):
    response = await app.state.http_client.get(
        "https://jsonplaceholder.typicode.com/posts"
    )
    return response.json()