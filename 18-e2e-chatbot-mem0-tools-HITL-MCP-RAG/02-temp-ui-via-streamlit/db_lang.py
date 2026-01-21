from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph.message import add_messages
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

# THIS LINE IS CRITICAL: It creates the 'checkpoints' tables in Postgres
checkpointer.setup() 

# --- 3. Custom Table for Persistent Titles ---
# LangGraph saves messages, but it doesn't provide an easy way to list all "Titles".
# We will create a simple table to store Thread ID + Readable Name.
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

# --- 4. Helper Functions for Frontend ---
def save_thread_title(thread_id, title):
    """Saves the title to Postgres so it survives reload."""
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO chat_metadata (thread_id, title) VALUES (%s, %s) ON CONFLICT (thread_id) DO UPDATE SET title = %s",
                (str(thread_id), title, title)
            )

def get_all_threads():
    """Fetches all previous chat threads from Postgres for the sidebar."""
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT thread_id, title FROM chat_metadata ORDER BY created_at DESC")
            return cur.fetchall() # Returns list of (thread_id, title) tuples

# --- 5. LangGraph Setup ---
llm = ChatOpenAI(model="gpt-4o-mini")

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState):
    messages = state['messages']
    response = llm.invoke(messages)
    return {"messages": [response]}

graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpointer)

# --- 6. Title Generator ---
def generate_conversation_title(user_content: str, ai_content: str) -> str:
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
    
# response = chatbot.invoke(
#     {
#         "messages": [HumanMessage(content="what is my name?")]
#     },
#     config = {'configurable': {'thread_id': "chat-1"}}
# )

# print(response)