from typing import TypedDict, List, Annotated
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    # Chat History (Appends new messages)
    messages: Annotated[List[BaseMessage], operator.add]
    
    # Context (From Frontend)
    current_url: str
    session_id: str
    
    # Internal Logic
    intent: str               # "technical", "pricing", "greeting"
    retrieved_docs: str       # The combined text of found documents
    buying_signal: bool       # True if user asks about cost/hiring
    
    # Lead Capture
    user_email: str | None
    email_status: str
    lead_captured: bool