from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import db
from app.services.graph_builder import chat_service
from app.api.chat import router as chat_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    await db.connect()                  # Await DB connection
    await chat_service.initialize_graph() # Await Graph setup
    yield
    # --- SHUTDOWN ---
    await db.close()                    # Await DB close

app = FastAPI(title="Hybrid Memory Bot", lifespan=lifespan)
app.include_router(chat_router, prefix="/api/v1", tags=["Chat"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)