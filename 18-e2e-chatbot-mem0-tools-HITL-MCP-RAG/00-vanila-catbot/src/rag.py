import os
import tempfile
from typing import Dict, Any, Optional
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_tavily import TavilySearch
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
load_dotenv()

# In-Memory Vector Store (Thread ID -> Retriever)
_THREAD_RETRIEVERS: Dict[str, Any] = {}
_THREAD_FILES: Dict[str, str] = {} # Map ID to Filename

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
llm_mini = ChatOpenAI(model="gpt-4o-mini")

def ingest_pdf(file_bytes: bytes, thread_id: str, filename: str) -> dict:
    if not file_bytes: return {"error": "Empty file"}

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(file_bytes)
        temp_path = temp_file.name

    try:
        loader = PyPDFLoader(temp_path)
        docs = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_documents(docs)

        if not chunks: return {"error": "No text extracted"}

        vector_store = FAISS.from_documents(chunks, embeddings)
        retriever = vector_store.as_retriever(search_kwargs={"k": 4})

        _THREAD_RETRIEVERS[str(thread_id)] = retriever
        _THREAD_FILES[str(thread_id)] = filename
        
        return {"status": "success", "chunks": len(chunks), "filename": filename}
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)

def get_current_filename(thread_id: str):
    return _THREAD_FILES.get(str(thread_id))

# --- TOOLS ---
tavily_tool = TavilySearch(max_results=3, topic="general")

@tool
def rag_tool(query: str, thread_id: str) -> str:
    """Search the uploaded PDF. You MUST pass the thread_id."""
    retriever = _THREAD_RETRIEVERS.get(str(thread_id))
    if not retriever: return "No PDF found. Ask user to upload one."
    docs = retriever.invoke(query)
    return "\n\n".join([d.page_content for d in docs])

ALL_TOOLS = [tavily_tool, rag_tool]

# --- TITLE GEN ---
async def generate_title(user_msg: str, ai_msg: str):
    try:
        res = await llm_mini.ainvoke([
            SystemMessage(content="Summarize into a 3-5 word title. No quotes."),
            HumanMessage(content=f"User: {user_msg}\nAI: {ai_msg}")
        ])
        return res.content.strip()
    except:
        return "New Chat"