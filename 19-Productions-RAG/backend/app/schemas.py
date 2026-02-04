from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str
    url: str                # Crucial for Context Awareness
    session_id: str
    user_email: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    action: Optional[str] = None # e.g., "capture_email"