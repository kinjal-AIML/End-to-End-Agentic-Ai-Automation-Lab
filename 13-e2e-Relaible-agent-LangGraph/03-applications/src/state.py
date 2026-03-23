from langgraph.graph import StateGraph
from typing import TypedDict, Literal
from pydantic import Field


class ReliableAgentState(TypedDict):
    query: str
    response: str
    pass