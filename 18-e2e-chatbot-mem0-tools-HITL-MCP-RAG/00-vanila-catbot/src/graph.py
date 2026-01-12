from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from src.state import ChatState
from src.nodes import chat_node

def build_graph():
    """
    Constructs and compiles the StateGraph.
    """
    # 1. Initialize Graph
    workflow = StateGraph(ChatState)

    # 2. Add Nodes
    workflow.add_node("chatbot", chat_node)

    # 3. Add Edges
    workflow.add_edge(START, "chatbot")
    workflow.add_edge("chatbot", END)

    # 4. Compile with Memory
    # Checkpointer allows us to keep chat history (thread_id)
    memory = InMemorySaver()
    graph = workflow.compile(checkpointer=memory)
    
    return graph