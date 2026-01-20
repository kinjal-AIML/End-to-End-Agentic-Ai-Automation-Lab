import streamlit as st
from langgraph_backend import chatbot, generate_conversation_title
from langchain_core.messages import HumanMessage, AIMessage
import uuid

# **************************************** utility functions *************************

def generate_thread_id():
    return uuid.uuid4()

def reset_chat():
    new_thread_id = generate_thread_id()
    st.session_state['thread_id'] = new_thread_id
    add_thread(new_thread_id)
    st.session_state['message_history'] = []

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def load_conversation(thread_id):
    state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
    return state.values.get('messages', [])

# **************************************** Session Setup ******************************

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = []

# Dictionary to store titles { uuid : "Title" }
if 'chat_titles' not in st.session_state:
    st.session_state['chat_titles'] = {}

add_thread(st.session_state['thread_id'])


# **************************************** Sidebar UI *********************************

st.sidebar.title('LangGraph Chatbot')

if st.sidebar.button('New Chat'):
    reset_chat()

st.sidebar.header('My Conversations')

# Display threads in reverse order (newest on top)
for thread_id in st.session_state['chat_threads'][::-1]:
    
    # Get title or default to 'New Chat'
    display_name = st.session_state['chat_titles'].get(thread_id, "New Chat")
    
    if st.sidebar.button(display_name, key=str(thread_id)):
        st.session_state['thread_id'] = thread_id
        messages = load_conversation(thread_id)

        temp_messages = []
        for msg in messages:
            role = 'user' if isinstance(msg, HumanMessage) else 'assistant'
            temp_messages.append({'role': role, 'content': msg.content})

        st.session_state['message_history'] = temp_messages


# **************************************** Main UI ************************************

# 1. Load History
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input = st.chat_input('Type here')

if user_input:
    current_thread_id = st.session_state['thread_id']

    # 2. Add User Message (Visual only first)
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    # 3. Generate & Stream AI Response
    CONFIG = {'configurable': {'thread_id': current_thread_id}}
    
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

    # 4. Save AI Message
    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})

    # 5. TITLE GENERATION LOGIC (Happens AFTER chat is done)
    # Only generate if this thread is named "New Chat" or doesn't exist in titles yet
    if current_thread_id not in st.session_state['chat_titles']:
        
        # We don't want a spinner here to disturb the user, just do it
        new_title = generate_conversation_title(user_input, ai_message)
        st.session_state['chat_titles'][current_thread_id] = new_title
        
        # We force a rerun so the Sidebar updates IMMEDIATELY after the message is done
        st.rerun()