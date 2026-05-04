import time
from fastapi import Request, HTTPException

RATE_LIMIT = 5       # requests
WINDOW_SIZE = 60     # seconds

## vanilla implementation
# async def rate_limiter(request: Request):
#     client_ip = request.client.host

#     key = f"rate_limit:{client_ip}"

#     # Get current count
#     current = await request.app.state.redis.get(key)

#     if current is None:
#         # First request → set count = 1 and expiry
#         await request.app.state.redis.set(key, 1, ex=WINDOW_SIZE)
#         return

#     current = int(current)

#     if current >= RATE_LIMIT:
#         raise HTTPException(
#             status_code=429,
#             detail="Rate limit exceeded. Try again later."
#         )

#     # Increment count
#     await request.app.state.redis.incr(key)

async def rate_limiter(request: Request):
    client_ip = request.client.host
    key = f"rate_limit:{client_ip}"

    count = await request.app.state.redis.incr(key)

    if count == 1:
        await request.app.state.redis.expire(key, WINDOW_SIZE)

    if count > RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded"
        )