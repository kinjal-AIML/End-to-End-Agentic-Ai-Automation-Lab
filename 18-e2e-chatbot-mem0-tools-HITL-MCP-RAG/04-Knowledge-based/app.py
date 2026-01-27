import streamlit as st
from rag_backend import (
    chatbot, 
    generate_conversation_title, 
    save_thread_title, 
    get_all_threads,
    ingest_pdf,
    thread_document_metadata
)
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
import uuid

# **************************************** Utility Functions *************************
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
    st.session_state['chat_threads'] = get_all_threads() 

# Helper to track if a file is already uploaded for the current UI session
if "ingested_docs" not in st.session_state:
    st.session_state["ingested_docs"] = {}

# **************************************** Sidebar UI *********************************
st.sidebar.title('LangGraph Chatbot')
st.sidebar.caption(f"Thread ID: {st.session_state['thread_id']}")

if st.sidebar.button('New Chat'):
    reset_chat()
    st.rerun()

# --- PDF UPLOADER SECTION ---
st.sidebar.divider()
st.sidebar.header("📄 Knowledge Base")

current_thread = st.session_state['thread_id']
doc_meta = thread_document_metadata(current_thread)

# Show current active document
if doc_meta:
    st.sidebar.success(f"Active: **{doc_meta.get('filename')}** ({doc_meta.get('chunks')} chunks)")
else:
    st.sidebar.info("No PDF uploaded for this chat.")

uploaded_pdf = st.sidebar.file_uploader("Upload PDF", type=["pdf"], key=f"uploader_{current_thread}")

if uploaded_pdf:
    # Check if we already processed this specific file for this thread to avoid re-processing
    is_processed = st.session_state["ingested_docs"].get(current_thread) == uploaded_pdf.name
    
    if not is_processed:
        with st.sidebar.status("Indexing PDF...", expanded=True) as status:
            file_bytes = uploaded_pdf.getvalue()
            result = ingest_pdf(file_bytes, current_thread, uploaded_pdf.name)
            
            # Mark as processed
            st.session_state["ingested_docs"][current_thread] = uploaded_pdf.name
            status.update(label="✅ Indexed Successfully", state="complete", expanded=False)
            st.rerun()

st.sidebar.divider()
st.sidebar.header('History')

# Sidebar History List
for t_id, t_title in st.session_state['chat_threads']:
    if st.sidebar.button(t_title, key=str(t_id)):
        st.session_state['thread_id'] = t_id
        messages = load_conversation(t_id)

        # Filter messages for clean UI (Hide ToolMessages)
        temp_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                temp_messages.append({'role': 'user', 'content': msg.content})
            elif isinstance(msg, AIMessage) and msg.content:
                temp_messages.append({'role': 'assistant', 'content': msg.content})

        st.session_state['message_history'] = temp_messages
        st.rerun()


# **************************************** Main UI ************************************
st.title("🤖 Agentic Chat (Web + PDF)")

for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input = st.chat_input('Ask about the web or your PDF...')

if user_input:
    # 1. UI: User Message
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    # 2. Logic: Stream Response
    CONFIG = {
        'configurable': {'thread_id': current_thread}
    }
    
    with st.chat_message("assistant"):
        status_box = st.status("Thinking...", expanded=True)
        
        def ai_only_stream():
            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode="messages"
            ):
                # A. Tool Call Notification
                if isinstance(message_chunk, AIMessage) and message_chunk.tool_calls:
                    tool_name = message_chunk.tool_calls[0]['name']
                    status_box.update(label=f"🛠️ Using Tool: {tool_name}", state="running")
                    status_box.write(f"Calling `{tool_name}`...")

                # B. Tool Output Notification
                elif isinstance(message_chunk, ToolMessage):
                    status_box.write(f"✅ Tool Result Received.")
                
                # C. Final Answer
                elif isinstance(message_chunk, AIMessage) and message_chunk.content:
                    status_box.update(label="Finished", state="complete", expanded=False)
                    yield message_chunk.content

        ai_message = st.write_stream(ai_only_stream())

    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})

    # 3. Logic: Title Generation & Saving to DB
    existing_ids = [t[0] for t in st.session_state['chat_threads']]

    if current_thread not in existing_ids:
        new_title = generate_conversation_title(user_input, ai_message)
        save_thread_title(current_thread, new_title)
        st.session_state['chat_threads'].insert(0, (current_thread, new_title))
        st.rerun()