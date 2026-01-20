from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import os
from urllib.parse import quote_plus
from psycopg_pool import ConnectionPool # Required for persistent connection

load_dotenv()

# --- 1. Database Connection Details ---
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("LANG_DB", "postgres")

encoded_password = quote_plus(DB_PASSWORD)

# --- 2. Construct the SQLAlchemy Connection String ---
DATABASE_URL = f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=disable"

# --- 3. Setup Postgres Checkpointer (Production Style) ---
# We create a connection pool so the connection stays open for Streamlit
pool = ConnectionPool(
    conninfo=DATABASE_URL,
    max_size=20,  # Allow up to 20 concurrent connections
    kwargs={"autocommit": True}
)

checkpointer = PostgresSaver(pool)

# IMPORTANT: This creates the necessary tables in Postgres if they don't exist.
# In a strict production environment, you might run this via a migration script, 
# but for now, we run it on startup.
checkpointer.setup()

# --- 4. Define the LLM ---
llm = ChatOpenAI(model="gpt-4o-mini")

# --- 5. Chat Graph Setup ---
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

# Compile with the Postgres checkpointer
chatbot = graph.compile(checkpointer=checkpointer)

# --- Improved Title Generator ---
def generate_conversation_title(user_content: str, ai_content: str) -> str:
    """
    Generates a title based on the interaction.
    """
    system_prompt = (
        "You are a helpful assistant that names conversation threads."
        "Based on the user's input and your response, generate a concise "
        "3-5 word title for this chat. "
        "Do not use quotes. Do not use the word 'Title'."
    )
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"User: {user_content}\nAI: {ai_content}")
    ]
    
    try:
        response = llm.invoke(messages)
        return response.content.strip()
    except Exception:
        return "New Conversation"