from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated, Dict, Any, Optional
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_tavily import TavilySearch
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.tools import tool
from dotenv import load_dotenv
import os
import tempfile
from urllib.parse import quote_plus
from psycopg_pool import ConnectionPool

load_dotenv()

# =========================== 1. Database Connection ===========================
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("LANG_DB", "postgres")

encoded_password = quote_plus(DB_PASSWORD)
DATABASE_URL = f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=disable"

pool = ConnectionPool(conninfo=DATABASE_URL, max_size=20, kwargs={"autocommit": True})
checkpointer = PostgresSaver(pool)
checkpointer.setup()

# =========================== 2. Custom Metadata Tables ===========================
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

# =========================== 3. RAG / Vector Store Logic ===========================
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# In-Memory storage for Retrievers (Note: If server restarts, these are lost, 
# but Postgres chat history remains. For production RAG, use pgvector)
_THREAD_RETRIEVERS: Dict[str, Any] = {}
_THREAD_METADATA: Dict[str, dict] = {}

def _get_retriever(thread_id: Optional[str]):
    return _THREAD_RETRIEVERS.get(str(thread_id))

def ingest_pdf(file_bytes: bytes, thread_id: str, filename: Optional[str] = None) -> dict:
    """Processes PDF and creates a FAISS retriever for the specific thread."""
    if not file_bytes:
        raise ValueError("No file uploaded")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(file_bytes)
        temp_path = temp_file.name

    try:
        loader = PyPDFLoader(temp_path)
        docs = loader.load()

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_documents(docs)

        if not chunks:
            return {"error": "No text found in PDF"}

        vector_store = FAISS.from_documents(chunks, embeddings)
        retriever = vector_store.as_retriever(search_kwargs={"k": 4})

        _THREAD_RETRIEVERS[str(thread_id)] = retriever
        _THREAD_METADATA[str(thread_id)] = {
            "filename": filename,
            "chunks": len(chunks)
        }
        
        return _THREAD_METADATA[str(thread_id)]
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def thread_document_metadata(thread_id: str) -> dict:
    return _THREAD_METADATA.get(str(thread_id), {})

# =========================== 4. Tools Definition ===========================

# Tool 1: Web Search
tavily_tool = TavilySearch(max_results=3, topic="general")

# Tool 2: RAG Tool
@tool
def rag_tool(query: str, thread_id: str) -> str:
    """
    Search the uploaded PDF document for relevant information. 
    You MUST provide the thread_id.
    """
    retriever = _get_retriever(thread_id)
    if not retriever:
        return "No document found. Ask the user to upload a PDF first."

    docs = retriever.invoke(query)
    return "\n\n".join([d.page_content for d in docs])

tools = [tavily_tool, rag_tool]

# =========================== 5. LangGraph Setup ===========================
llm = ChatOpenAI(model="gpt-4o-mini")
llm_with_tools = llm.bind_tools(tools)

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState, config):
    """
    The main Chat Node. We inject the thread_id into the system prompt
    so the LLM knows how to call the rag_tool correctly.
    """
    thread_id = config.get("configurable", {}).get("thread_id")
    
    system_msg = SystemMessage(content=(
        "You are a helpful assistant. "
        "You have access to a web search tool and a PDF RAG tool. "
        "If the user asks about the 'uploaded document', use the `rag_tool`. "
        f"When using `rag_tool`, you MUST pass this thread_id: '{thread_id}'. "
        "If the user asks general questions, use `tavily_search_results_json`. "
    ))
    
    # Prepend system message to history
    messages = [system_msg] + state['messages']
    
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

# Tool Node
tool_node = ToolNode(tools)

# Graph Construction
graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "chat_node")
graph.add_conditional_edges("chat_node", tools_condition)
graph.add_edge("tools", "chat_node")

chatbot = graph.compile(checkpointer=checkpointer)

# =========================== 6. Title Generator ===========================
def generate_conversation_title(user_content: str, ai_content: str) -> str:
    if not ai_content: ai_content = "Tool Usage"
    messages = [
        SystemMessage(content="Generate a 3-5 word title. No quotes."),
        HumanMessage(content=f"User: {user_content}\nAI: {ai_content}")
    ]
    try:
        return llm.invoke(messages).content.strip()
    except:
        return "New Conversation"