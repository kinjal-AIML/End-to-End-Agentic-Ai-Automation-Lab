from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.state import AgentState
from app.graph.nodes import router_node, retriever_node, generator_node, lead_capture_node

def route_intent(state: AgentState):
    """
    Determines where to go after the Router Node.
    """
    intent = state["intent"]
    
    # LOGIC UPDATE: 
    # 'CONTACT' is added here because contact questions often require 
    # facts (Address, Process, Email) from the CSV files.
    if intent in ["TECHNICAL", "COMPANY", "PRICING", "CONTACT"]:
        return "retrieve" 
        
    # 'GREETING' and 'OFF_TOPIC' skip retrieval to save time/cost.
    return "capture"

workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("router", router_node)
workflow.add_node("retrieve", retriever_node)
workflow.add_node("capture", lead_capture_node) # New Node
workflow.add_node("generate", generator_node)

# Entry
workflow.set_entry_point("router")

# ... inside workflow setup ...

# 1. Router -> (Retrieve OR Capture)
workflow.add_conditional_edges(
    "router",
    route_intent,
    {
        "retrieve": "retrieve",
        "capture": "capture"
    }
)

# 2. Retrieve -> Capture
# (After reading docs, we pass to capture to check for email)
workflow.add_edge("retrieve", "capture")

# 3. Capture -> Generate
# (After checking email, we generate the response)
workflow.add_edge("capture", "generate")

# 4. Generate -> End
workflow.add_edge("generate", END)

checkpointer = MemorySaver()
app_graph = workflow.compile(checkpointer=checkpointer)