import logging
from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatRequest, ChatResponse
from app.services.graph_builder import chat_service
import traceback # <--- Add this to see stack traces

logger = logging.getLogger("uvicorn")
router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        response_text = await chat_service.process_message(
            user_id=request.user_id,
            thread_id=request.thread_id,
            message=request.message
        )
        return ChatResponse(response=response_text)
    except Exception as e:
        # Print the FULL error to your terminal
        error_details = traceback.format_exc()
        logger.error(f"🔥 API ERROR:\n{error_details}")
        
        # Return the error message to the client (for debugging)
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")