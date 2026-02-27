import uuid
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, RemoveMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from app.models.state import AgentState
from app.models.schemas import MemoryOutput
from app.utils.prompts import MEMORY_SYSTEM_PROMPT, CHAT_SYSTEM_PROMPT, SUMMARY_PROMPT

logger = logging.getLogger("uvicorn")

fast_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
smart_llm = ChatOpenAI(model="gpt-4o", temperature=0)

# --- Node 1: LTM Manager (Async) ---
async def ltm_node(state: AgentState, config: RunnableConfig, *, store: BaseStore):
    user_id = config["configurable"]["user_id"]
    namespace = ("user", user_id, "profile")
    
    # 1. Fetch (Async)
    items = await store.asearch(namespace) # <--- Changed to asearch
    existing_text = "\n".join([f"ID: {i.key} | Fact: {i.value['data']}" for i in items]) if items else "(Empty)"

    # 2. Analyze
    last_msg = state["messages"][-1]
    if isinstance(last_msg, HumanMessage):
        extractor = smart_llm.with_structured_output(MemoryOutput)
        decision = await extractor.ainvoke([ # <--- ainvoke for async LLM
            SystemMessage(content=MEMORY_SYSTEM_PROMPT.format(
                existing_memories=existing_text, 
                user_message=last_msg.content
            ))
        ])

        # 3. Write (Async)
        if decision.operations:
            logger.info(f"🧠 LTM Logic: {decision.thoughts}")
            for op in decision.operations:
                if op.action == "create" and op.content:
                    await store.aput(namespace, str(uuid.uuid4()), {"data": op.content}) # <--- aput
                elif op.action == "update" and op.memory_id and op.content:
                    await store.aput(namespace, op.memory_id, {"data": op.content}) # <--- aput
                elif op.action == "delete" and op.memory_id:
                    await store.adelete(namespace, op.memory_id) # <--- adelete
            
            # Refetch
            items = await store.asearch(namespace) # <--- asearch
            existing_text = "\n".join([f"- {i.value['data']}" for i in items])
    
    return {"user_profile": existing_text}

# --- Node 2: Chat Generator (Async) ---
async def chat_node(state: AgentState, config: RunnableConfig, *, store: BaseStore):
    profile_text = state.get("user_profile", "No known details.")
    current_summary = state.get("summary", "No summary yet.")

    system_msg = SystemMessage(content=CHAT_SYSTEM_PROMPT.format(
        user_profile=profile_text,
        summary=current_summary
    ))
    
    response = await fast_llm.ainvoke([system_msg] + state["messages"]) # <--- ainvoke
    return {"messages": [response]}

# --- Node 3: STM Summarizer (Async) ---
async def summarize_node(state: AgentState):
    messages = state["messages"]
    summary = state.get("summary", "")

    if len(messages) > 6:
        logger.info("🧹 Summarizing conversation history...")
        to_summarize = messages[:-2]
        
        prompt = SUMMARY_PROMPT.format(
            existing_summary=summary if summary else "None",
            new_lines="\n".join([f"{m.type}: {m.content}" for m in to_summarize])
        )
        
        new_summary_msg = await fast_llm.ainvoke(prompt) # <--- ainvoke
        
        return {
            "summary": new_summary_msg.content,
            "messages": [RemoveMessage(id=m.id) for m in to_summarize]
        }
    
    return {}