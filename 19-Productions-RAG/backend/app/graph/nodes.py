from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from app.state import AgentState
from app.config import Config
from app.prompts import ROUTER_SYSTEM_PROMPT, get_architect_prompt, LEAD_CAPTURE_PROMPT
from app.services.llm import router_llm, generator_llm
from app.services.vector import retriever_service


import re
from app.prompts import ROUTER_SYSTEM_PROMPT, get_architect_prompt
from app.services.llm import router_llm, generator_llm
from app.services.vector import retriever_service
from app.services.email import send_lead_alert

# --- NODE 1: ROUTER (The Traffic Controller) ---
def router_node(state: AgentState):
    """
    Analyzes the latest message and decides the next step.
    Uses the fast 'gpt-4o-mini' model.
    """
    print("--- ROUTER NODE ---")
    messages = state["messages"]
    
    # CRITICAL FOR MEMORY: 
    # Since 'messages' contains the whole history, we only want to analyze 
    # the VERY LAST message to determine the current intent.
    last_message = messages[-1]
    
    # Call Router LLM
    response = router_llm.invoke([
        SystemMessage(content=ROUTER_SYSTEM_PROMPT),
        last_message
    ])
    
    intent = response.content.strip().upper()
    print(f"Detected Intent: {intent}")
    
    # Update State
    return {"intent": intent}


# --- NODE 2: RETRIEVER (The Librarian) ---
def retriever_node(state: AgentState):
    """
    Fetches documents using our Custom RRF Hybrid Search.
    Only runs if the intent requires knowledge.
    """
    print("--- RETRIEVER NODE ---")
    messages = state["messages"]
    
    # CRITICAL FOR MEMORY:
    # We search based on the user's latest question, not the whole history.
    last_user_message = messages[-1].content
    
    # Use our Singleton Service
    context_str = retriever_service.retrieve(last_user_message)
    
    print(f"Retrieved {len(context_str)} chars of context.")
    
    return {"retrieved_docs": context_str}




# ... (Router and Retriever nodes remain the same) ...

# --- NODE 4: LEAD CAPTURE (The Closer) ---
async def lead_capture_node(state: AgentState):
    """
    Analyzes the LAST message. 
    If it contains an email, sends a Lead Alert to Admin.
    """
    print("--- LEAD CAPTURE NODE ---")
    messages = state["messages"]
    last_message = messages[-1].content
    current_url = state["current_url"]
    
    # 1. Regex to find email address
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(email_pattern, last_message)
    
    if match:
        extracted_email = match.group(0)
        print(f"📧 Email Detected: {extracted_email}")
        
        # 2. Generate a quick summary of the chat for the Admin
        # (We use the last 3 messages as context)
        chat_context = "\n".join([m.content for m in messages[-3:]])
        
        # 3. Send Email to Admin
        success = await send_lead_alert(
            user_email=extracted_email, 
            page_source=current_url, 
            summary=chat_context
        )
        
        if success:
            return {"email_status": "sent", "user_email": extracted_email}
        else:
            return {"email_status": "error"}
            
    else:
        # No email found in the last message
        return {"email_status": "none"}


# --- NODE 3: GENERATOR (The Architect) ---
async def generator_node(state: AgentState):
    """
    Generates the final response using GPT-4o.
    Dynamically swaps the System Prompt based on Email Status.
    """
    print("--- GENERATOR NODE ---")
    
    # 1. Load Data
    messages = state["messages"]
    current_url = state["current_url"]
    context = state.get("retrieved_docs", "")
    intent = state.get("intent", "GENERAL")
    email_status = state.get("email_status", "none") # 'sent', 'none', 'error'
    
    # 2. Get Base Prompt
    system_instruction = get_architect_prompt(current_url)
    
    # 3. Inject Context
    if context:
        system_instruction += f"\n\nRETRIEVED_CONTEXT:\n{context}"

    # 4. HANDLE EMAIL LOGIC (The most important part)
    
    if email_status == "sent":
        # Scenario: We just successfully emailed the admin.
        # Instruction: Tell the user we got it.
        system_instruction += """
        \n\nSYSTEM UPDATE: You have successfully captured the user's email and notified the BYV Engineering Team.
        YOUR RESPONSE:
        1. Thank the user professionally.
        2. Confirm that a Principal Engineer will review their request.
        3. Do NOT ask for the email again.
        4. Ask if they have any other technical questions in the meantime.
        """
        
    elif intent in ["PRICING", "CONTACT", "SALES"] and email_status == "none":
        # Scenario: User wants to buy, but hasn't given email yet.
        # Instruction: Ask for the email.
        system_instruction += """
        \n\nIMPORTANT SALES PROTOCOL:
        The user is asking about PRICING, HIRING, or CONTACT.
        You MUST ask for their email address to send a formal quote or schedule a meeting.
        Phrase it like: "I can prepare a custom architecture proposal. What is the best email to send it to?"
        """
        
    elif email_status == "error":
         system_instruction += "\n\nSYSTEM UPDATE: You tried to save the email but there was a system error. Ask the user to email 'contact@byvbd.com' directly."

    # 5. Call Generator LLM
    prompt_messages = [SystemMessage(content=system_instruction)] + messages
    response = await generator_llm.ainvoke(prompt_messages) # Using Async invoke
    
    return {"messages": [response]}