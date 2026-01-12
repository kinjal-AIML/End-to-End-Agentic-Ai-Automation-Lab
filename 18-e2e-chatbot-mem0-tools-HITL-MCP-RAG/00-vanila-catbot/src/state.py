from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class ChatState(TypedDict):
    # add_messages: automatically appends new messages to the list
    messages: Annotated[list[BaseMessage], add_messages]