from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, SystemMessage
from src.rag import ALL_TOOLS
from src.prompts import SYSTEM_PROMPT

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0) # Low temperature for professional output
llm_with_tools = llm.bind_tools(ALL_TOOLS)

def chat_node(state: ChatState, config):
    thread_id = config.get("configurable", {}).get("thread_id")
    
    # Inject dynamic system prompt
    sys_msg = SystemMessage(content=SYSTEM_PROMPT.format(thread_id=thread_id))
    
    # Ensure the system message is always at the top
    input_messages = [sys_msg] + state["messages"]
    return {"messages": [llm_with_tools.invoke(input_messages)]}

def build_graph(checkpointer):
    graph = StateGraph(ChatState)
    graph.add_node("chat_node", chat_node)
    graph.add_node("tools", ToolNode(ALL_TOOLS))
    
    graph.add_edge(START, "chat_node")
    graph.add_conditional_edges("chat_node", tools_condition)
    graph.add_edge("tools", "chat_node")
    
    return graph.compile(checkpointer=checkpointer)