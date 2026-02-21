import uuid
import os
from typing import List, Optional, Literal
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.store.postgres import PostgresStore
from langgraph.store.base import BaseStore

# Load environment variables
load_dotenv()

# ==========================================
# 1. DEFINE SCHEMAS FOR CRUD OPERATIONS
# ==========================================

class MemoryOp(BaseModel):
    """A single operation to modify the user's long-term memory."""
    action: Literal["create", "update", "delete"] = Field(
        description="The action to perform. 'create' for new info, 'update' to correct existing info, 'delete' to remove obsolete info."
    )
    memory_id: Optional[str] = Field(
        default=None, 
        description="The UUID of the existing memory to update or delete. Required for 'update' and 'delete'. Ignored for 'create'."
    )
    content: Optional[str] = Field(
        default=None, 
        description="The content of the memory. Required for 'create' and 'update'. Ignored for 'delete'."
    )

class MemoryOutput(BaseModel):
    """The collection of memory operations to perform."""
    thoughts: str = Field(description="Your reasoning for why you are making these changes.")
    operations: List[MemoryOp] = Field(default_factory=list)

# ==========================================
# 2. SETUP LLMS & PROMPTS
# ==========================================

# A. Memory Management LLM (Needs to be smart, GPT-4o or GPT-4o-mini is good)
memory_llm = ChatOpenAI(model="gpt-4o", temperature=0)
memory_extractor = memory_llm.with_structured_output(MemoryOutput)

MEMORY_SYSTEM_PROMPT = """You are a Long-Term Memory Manager. 
Your goal is to maintain an accurate, up-to-date list of facts about the user.

You have access to the CURRENT MEMORIES with their IDs.
Your task is to listen to the USER'S LATEST MESSAGE and determine if the memory needs changes.

RULES:
1. **CREATE**: If the user provides NEW information not in the list, create a new memory.
2. **UPDATE**: If the user updates specific information (e.g., moved from City A to City B), use the ID of the old memory to UPDATE it.
3. **DELETE**: If a memory is explicitly stated as wrong or no longer true, and no replacement is needed, DELETE it using its ID.
4. **NO CHANGE**: If the info is already there, do nothing.

Output a list of operations. Keep memory content atomic (one fact per item).
"""

# B. Chat Bot LLM
chat_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

CHAT_SYSTEM_PROMPT = """You are a helpful assistant.
You have access to the user's long-term memory below. 
Use this context to personalize your response.

--- USER MEMORIES ---
{user_details}
---------------------
"""

# ==========================================
# 3. DEFINE GRAPH NODES
# ==========================================

def remember_node(state: MessagesState, config: RunnableConfig, *, store: BaseStore):
    """
    Reads current memories, checks for updates based on new messages, 
    and performs CRUD operations on the Postgres Store.
    """
    user_id = config["configurable"]["user_id"]
    namespace = ("user", user_id, "details")

    # 1. Fetch existing memories with their IDs
    items = store.search(namespace)
    
    # Format for the LLM: "ID: <uuid> | Content: <text>"
    existing_memories_text = ""
    if items:
        for item in items:
            existing_memories_text += f"ID: {item.key} | Content: {item.value['data']}\n"
    else:
        existing_memories_text = "(No existing memories)"

    # 2. Prepare Prompt
    latest_msg = state["messages"][-1].content
    
    prompt = f"""
    CURRENT MEMORIES:
    {existing_memories_text}

    USER'S LATEST MESSAGE:
    "{latest_msg}"
    
    Decide the necessary operations.
    """

    # 3. Invoke LLM
    decision: MemoryOutput = memory_extractor.invoke([
        SystemMessage(content=MEMORY_SYSTEM_PROMPT),
        {"role": "user", "content": prompt}
    ])

    # 4. Execute Operations on Postgres
    print(f"\n🧠 [Memory Logic]: {decision.thoughts}")
    
    for op in decision.operations:
        if op.action == "create" and op.content:
            new_id = str(uuid.uuid4())
            store.put(namespace, new_id, {"data": op.content})
            print(f"   ➕ Created: {op.content}")
            
        elif op.action == "update" and op.memory_id and op.content:
            # We overwrite the existing key
            store.put(namespace, op.memory_id, {"data": op.content})
            print(f"   🔄 Updated ID {op.memory_id}: {op.content}")
            
        elif op.action == "delete" and op.memory_id:
            store.delete(namespace, op.memory_id)
            print(f"   ❌ Deleted ID {op.memory_id}")

    return {}

def chat_node(state: MessagesState, config: RunnableConfig, *, store: BaseStore):
    """
    Standard chat node that reads memory just for context.
    """
    user_id = config["configurable"]["user_id"]
    namespace = ("user", user_id, "details")
    
    items = store.search(namespace)
    user_details = "\n".join([f"- {item.value['data']}" for item in items]) if items else "(No information yet)"
    
    system_msg = SystemMessage(content=CHAT_SYSTEM_PROMPT.format(user_details=user_details))
    response = chat_llm.invoke([system_msg] + state["messages"])
    
    return {"messages": [response]}

# ==========================================
# 4. BUILD THE GRAPH
# ==========================================

builder = StateGraph(MessagesState)
builder.add_node("remember", remember_node)
builder.add_node("chat", chat_node)

builder.add_edge(START, "remember")
builder.add_edge("remember", "chat")
builder.add_edge("chat", END)

# ==========================================
# 5. EXECUTION (SIMULATION)
# ==========================================

# Replace with your actual DB Connection String
DB_URI = "postgresql://postgres:postgres@localhost:5442/postgres?sslmode=disable"

# Verify we can connect and run
try:
    with PostgresStore.from_conn_string(DB_URI) as store:
        store.setup() # Ensure tables exist
        graph = builder.compile(store=store)
        
        config = {"configurable": {"user_id": "test_user_001"}}

        print("\n--- Interaction 1: Introduction ---")
        graph.invoke({"messages": [{"role": "user", "content": "Hi, I am Al Amin and I live in Gulshan, Dhaka."}]}, config)

        print("\n--- Interaction 2: Correction (The Update Test) ---")
        # This should trigger an UPDATE or DELETE+CREATE operation, not just a duplicate add
        graph.invoke({"messages": [{"role": "user", "content": "Actually, I moved. I now live in Sylhet."}]}, config)

        print("\n--- Interaction 3: Query ---")
        response = graph.invoke({"messages": [{"role": "user", "content": "Where do I live?"}]}, config)
        print(f"\n🤖 BOT: {response['messages'][-1].content}")

        print("\n--- Final Database State ---")
        items = store.search(("user", "test_user_001", "details"))
        for item in items:
            print(f"[{item.key}]: {item.value['data']}")

except Exception as e:
    print("Error connecting to DB or running graph. Check your Docker/DB settings.")
    print(e)