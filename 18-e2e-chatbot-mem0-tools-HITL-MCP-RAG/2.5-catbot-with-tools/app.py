import streamlit as st
from langgraph_backend import (
    chatbot, 
    generate_conversation_title, 
    save_thread_title, 
    get_all_threads
)
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
import uuid

# **************************************** utility functions *************************

def generate_thread_id():
    return str(uuid.uuid4())

def reset_chat():
    new_thread_id = generate_thread_id()
    st.session_state['thread_id'] = new_thread_id
    st.session_state['message_history'] = []

def load_conversation(thread_id):
    state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
    return state.values.get('messages', [])

# **************************************** Session Setup ******************************

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    db_threads = get_all_threads() 
    st.session_state['chat_threads'] = db_threads 

# **************************************** Sidebar UI *********************************

st.sidebar.title('LangGraph Chatbot')

if st.sidebar.button('New Chat'):
    reset_chat()

st.sidebar.header('History')

for t_id, t_title in st.session_state['chat_threads']:
    if st.sidebar.button(t_title, key=str(t_id)):
        st.session_state['thread_id'] = t_id
        messages = load_conversation(t_id)

        # Convert back to UI format
        # Filter: Don't show ToolMessages or ToolCalls in the history view (keeps it clean)
        temp_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                temp_messages.append({'role': 'user', 'content': msg.content})
            elif isinstance(msg, AIMessage) and msg.content:
                # Only add AI messages that have actual text content
                temp_messages.append({'role': 'assistant', 'content': msg.content})

        st.session_state['message_history'] = temp_messages


# **************************************** Main UI ************************************

for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input = st.chat_input('Type here')

if user_input:
    current_thread_id = st.session_state['thread_id']

    # 1. UI: User Message
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    # 2. Logic: Stream Response with Status for Tools
    CONFIG = {
        'configurable': {'thread_id': current_thread_id}
    }
    
    with st.chat_message("assistant"):
        
        # Create a status container for tool outputs
        status_container = st.status("Thinking...", expanded=True)
        
        def ai_only_stream():
            # stream_mode="messages" returns every message generated (AI, Tools, etc.)
            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode="messages"
            ):
                # 1. Handle Tool Calls (AI deciding to use a tool)
                if isinstance(message_chunk, AIMessage) and message_chunk.tool_calls:
                    tool_name = message_chunk.tool_calls[0]['name']
                    status_container.write(f"🛠️ Calling tool: **{tool_name}**...")
                
                # 2. Handle Tool Outputs (The result from the tool)
                elif isinstance(message_chunk, ToolMessage):
                    status_container.write(f"✅ Tool result received.")
                
                # 3. Handle Final AI Response (Text)
                elif isinstance(message_chunk, AIMessage) and message_chunk.content:
                    # Once we start getting text, we can close the status container
                    status_container.update(label="Finished", state="complete", expanded=False)
                    yield message_chunk.content

        # write_stream consumes the generator and types out the final answer
        ai_message = st.write_stream(ai_only_stream())

    # 3. Save AI Message to History State
    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})

    # 4. Title Generation
    existing_ids = [t[0] for t in st.session_state['chat_threads']]
    if current_thread_id not in existing_ids:
        new_title = generate_conversation_title(user_input, ai_message)
        save_thread_title(current_thread_id, new_title)
        st.session_state['chat_threads'].insert(0, (current_thread_id, new_title))
        st.rerun()