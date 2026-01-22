import streamlit as st
from db_lang import (
    chatbot, 
    generate_conversation_title, 
    save_thread_title, 
    get_all_threads
)
from langchain_core.messages import HumanMessage, AIMessage
import uuid

# **************************************** utility functions *************************

def generate_thread_id():
    return str(uuid.uuid4())

def reset_chat():
    new_thread_id = generate_thread_id()
    st.session_state['thread_id'] = new_thread_id
    # We do NOT add to list immediately. We wait until a message is sent.
    st.session_state['message_history'] = []

def load_conversation(thread_id):
    # Fetch from LangGraph Postgres Memory
    state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
    return state.values.get('messages', [])

# **************************************** Session Setup ******************************

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

# --- CRITICAL FIX: Load existing threads from DB on startup ---
if 'chat_threads' not in st.session_state:
    # Format: [(uuid, "Title"), (uuid, "Title")]
    db_threads = get_all_threads() 
    st.session_state['chat_threads'] = db_threads 

# **************************************** Sidebar UI *********************************

st.sidebar.title('LangGraph Chatbot')

if st.sidebar.button('New Chat'):
    reset_chat()

st.sidebar.header('History')

# Display threads from Database (saved in session state)
# Tuple format from DB is (thread_id, title)
for t_id, t_title in st.session_state['chat_threads']:
    
    if st.sidebar.button(t_title, key=str(t_id)):
        st.session_state['thread_id'] = t_id
        messages = load_conversation(t_id)

        # Convert back to UI format
        temp_messages = []
        for msg in messages:
            role = 'user' if isinstance(msg, HumanMessage) else 'assistant'
            temp_messages.append({'role': role, 'content': msg.content})

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

    # 2. Logic: Stream Response
    CONFIG = {
        'configurable': {'thread_id': current_thread_id},
        "metadata": {
            "thread_id": st.session_state["thread_id"]
        },
        "run_name": "catbot"
        }
    
    with st.chat_message("assistant"):
        def ai_only_stream():
            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode="messages"
            ):
                if isinstance(message_chunk, AIMessage):
                    yield message_chunk.content

        ai_message = st.write_stream(ai_only_stream())

    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})

    # 3. Logic: Title Generation & Saving to DB
    # Check if this thread ID is already known in our session list
    # extracting just IDs from the list of tuples
    existing_ids = [t[0] for t in st.session_state['chat_threads']]

    if current_thread_id not in existing_ids:
        # Generate Title
        new_title = generate_conversation_title(user_input, ai_message)
        
        # Save to Postgres (So it survives reload)
        save_thread_title(current_thread_id, new_title)
        
        # Update Session State (So sidebar updates immediately)
        st.session_state['chat_threads'].insert(0, (current_thread_id, new_title))
        
        st.rerun()