from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from src.state import ChatState
import os
from dotenv import load_dotenv
load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
# Initialize LLM with streaming=True
# llm = ChatOpenAI(model="gpt-4o-mini", streaming=True)
llm = ChatGroq(model="openai/gpt-oss-120b")

def chat_node(state: ChatState):
    """
    This function receives the current state, invokes the LLM,
    and returns the new message to append to the state.
    """
    messages = state["messages"]
    
    # We simply invoke the model. 
    # The actual streaming to the console happens in main.py 
    # via the graph.stream_events method.
    response = llm.invoke(messages)
    
    return {
        "messages": [response]
    }