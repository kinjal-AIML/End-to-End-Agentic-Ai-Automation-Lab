from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import add_messages
from dotenv import load_dotenv

load_dotenv()

# Define the LLM
llm = ChatOpenAI(model="gpt-4o-mini")

# --- Chat Graph Setup ---
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState):
    messages = state['messages']
    response = llm.invoke(messages)
    return {"messages": [response]}

checkpointer = InMemorySaver()

graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpointer)

# --- NEW: Improved Title Generator ---
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
    
    # We provide both the user query and the AI response for context
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"User: {user_content}\nAI: {ai_content}")
    ]
    
    try:
        response = llm.invoke(messages)
        return response.content.strip()
    except Exception:
        return "New Conversation"