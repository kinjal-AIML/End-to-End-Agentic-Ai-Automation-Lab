from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_tavily import TavilySearch
from dotenv import load_dotenv
import os
from urllib.parse import quote_plus
from psycopg_pool import ConnectionPool

load_dotenv()

# --- 1. Database Connection ---
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("LANG_DB", "postgres")

encoded_password = quote_plus(DB_PASSWORD)
DATABASE_URL = f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=disable"

# --- 2. Connection Pool & Setup ---
pool = ConnectionPool(conninfo=DATABASE_URL, max_size=20, kwargs={"autocommit": True})
checkpointer = PostgresSaver(pool)
checkpointer.setup()

# --- 3. Custom Table for Titles ---
def ensure_custom_tables():
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_metadata (
                    thread_id TEXT PRIMARY KEY,
                    title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
ensure_custom_tables()

# --- 4. Helper Functions ---
def save_thread_title(thread_id, title):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO chat_metadata (thread_id, title) VALUES (%s, %s) ON CONFLICT (thread_id) DO UPDATE SET title = %s",
                (str(thread_id), title, title)
            )

def get_all_threads():
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT thread_id, title FROM chat_metadata ORDER BY created_at DESC")
            return cur.fetchall()

# --- 5. Tool Setup ---
search_tool = TavilySearch(max_results=3, topic="general")
tools = [search_tool]

# --- 6. LangGraph Setup ---
llm = ChatOpenAI(model="gpt-4o-mini")
llm_with_tools = llm.bind_tools(tools)

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState):
    messages = state['messages']
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

# Define Tool Node
tool_node = ToolNode(tools)

graph = StateGraph(ChatState)

# Add Nodes
graph.add_node("chat_node", chat_node)
graph.add_node("tools", tool_node)

# Add Edges
graph.add_edge(START, "chat_node")
graph.add_conditional_edges(
    "chat_node",
    tools_condition, # This automatically decides if it goes to "tools" or END
)
graph.add_edge("tools", "chat_node") # Loop back to LLM after tool use

chatbot = graph.compile(checkpointer=checkpointer)

# --- 7. Title Generator ---
def generate_conversation_title(user_content: str, ai_content: str) -> str:
    # If the AI content is empty (e.g. just a tool call), provide a fallback
    if not ai_content:
        ai_content = "Tool Usage"
        
    system_prompt = "Generate a 3-5 word title for this chat. No quotes."
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"User: {user_content}\nAI: {ai_content}")
    ]
    try:
        response = llm.invoke(messages)
        return response.content.strip()
    except Exception:
        return "New Conversation"