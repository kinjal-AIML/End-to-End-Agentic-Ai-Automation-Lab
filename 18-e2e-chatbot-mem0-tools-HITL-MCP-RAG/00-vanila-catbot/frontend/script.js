let currentThreadId = localStorage.getItem('thread_id') || generateUUID();
const chatBox = document.getElementById('chat-box');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const historyList = document.getElementById('history-list');
const dropZone = document.getElementById('drop-zone');
const dragOverlay = document.getElementById('drag-overlay');

// Markdown Configuration
marked.setOptions({ gfm: true, breaks: true });

document.addEventListener('DOMContentLoaded', () => {
    loadThreads();
    if(localStorage.getItem('thread_id')) {
        loadConversation(currentThreadId);
    }
});

// --- DRAG AND DROP ---
window.addEventListener('dragenter', (e) => {
    e.preventDefault();
    dragOverlay.classList.add('active');
});

dragOverlay.addEventListener('dragleave', (e) => {
    e.preventDefault();
    dragOverlay.classList.remove('active');
});

dragOverlay.addEventListener('dragover', (e) => e.preventDefault());

dragOverlay.addEventListener('drop', (e) => {
    e.preventDefault();
    dragOverlay.classList.remove('active');
    const files = e.dataTransfer.files;
    if (files.length > 0 && files[0].type === 'application/pdf') {
        handleFileUpload(files[0]);
    }
});

// --- CHAT LOGIC ---
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const message = userInput.value.trim();
    if (!message) return;

    appendMessage('user', message);
    userInput.value = '';

    const aiContainer = createMessageContainer('ai');
    let fullMarkdown = "";
    let currentToolElement = null;
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, thread_id: currentThreadId })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop();

            for (const line of lines) {
                if (!line.trim()) continue;
                const data = JSON.parse(line);
                
                if (data.type === 'tool_start') {
                    currentToolElement = showToolStatus(data.name, aiContainer.wrapper);
                } else if (data.type === 'content') {
                    // Remove tool spinner when words start appearing
                    if (currentToolElement) {
                        currentToolElement.remove();
                        currentToolElement = null;
                    }
                    fullMarkdown += data.chunk;
                    aiContainer.contentDiv.innerHTML = marked.parse(fullMarkdown);
                    scrollToBottom();
                } else if (data.type === 'title_update') {
                    loadThreads();
                }
            }
        }
    } catch (err) {
        aiContainer.contentDiv.innerText = "Error: Connection lost.";
    }
});

// --- UI HELPERS ---

function appendMessage(role, text) {
    const container = createMessageContainer(role);
    container.contentDiv.innerHTML = role === 'ai' ? marked.parse(text) : text;
    scrollToBottom();
}

function createMessageContainer(role) {
    const wrapper = document.createElement('div');
    wrapper.className = `message ${role}-message animate-in`;
    
    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.innerHTML = role === 'ai' ? '<i class="fa-solid fa-robot"></i>' : '<i class="fa-solid fa-user"></i>';
    
    const content = document.createElement('div');
    content.className = 'content';
    
    wrapper.appendChild(avatar);
    wrapper.appendChild(content);
    chatBox.appendChild(wrapper);
    return { wrapper, contentDiv: content };
}

function showToolStatus(toolName, messageWrapper) {
    const status = document.createElement('div');
    status.className = 'tool-usage';
    const nameMap = { 'rag_tool': 'Consulting PDF...', 'tavily_search_results_json': 'Searching Web...' };
    status.innerHTML = `<span class="loader"></span> ${nameMap[toolName] || toolName}`;
    chatBox.insertBefore(status, messageWrapper);
    scrollToBottom();
    return status;
}

// --- FILE UPLOAD ---
document.getElementById('upload-btn').addEventListener('click', () => document.getElementById('pdf-upload').click());
document.getElementById('pdf-upload').addEventListener('change', (e) => handleFileUpload(e.target.files[0]));

async function handleFileUpload(file) {
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    formData.append('thread_id', currentThreadId);

    const statusDiv = document.getElementById('upload-status');
    statusDiv.innerHTML = `<span style="font-size:0.8rem; color:var(--accent)"><i class="fa-solid fa-circle-notch fa-spin"></i> Processing ${file.name}...</span>`;

    try {
        const res = await fetch('/api/upload', { method: 'POST', body: formData });
        const result = await res.json();
        
        if (result.filename) {
            statusDiv.innerHTML = `<span style="font-size:0.8rem; color:#4ade80"><i class="fa-solid fa-check"></i> Indexed ${file.name}</span>`;
            document.getElementById('filename-display').innerText = result.filename;
            document.getElementById('active-file-indicator').classList.remove('hidden');
            setTimeout(() => { statusDiv.innerHTML = ""; }, 3000);
        }
    } catch (err) {
        statusDiv.innerText = "Upload failed.";
    }
}

async function loadConversation(id) {
    currentThreadId = id;
    localStorage.setItem('thread_id', id);
    chatBox.innerHTML = ''; 
    loadThreads(); 

    const res = await fetch(`/api/history/${id}`);
    const data = await res.json();
    
    data.messages.forEach(msg => {
        const container = createMessageContainer(msg.role === 'human' ? 'user' : 'ai');
        container.contentDiv.innerHTML = marked.parse(msg.content);
    });

    if (data.filename) {
        document.getElementById('filename-display').innerText = data.filename;
        document.getElementById('active-file-indicator').classList.remove('hidden');
    } else {
        document.getElementById('active-file-indicator').classList.add('hidden');
    }
    scrollToBottom();
}

async function loadThreads() {
    const res = await fetch('/api/threads');
    const threads = await res.json();
    historyList.innerHTML = '';
    threads.forEach(t => {
        const div = document.createElement('div');
        div.className = `history-item ${t.id === currentThreadId ? 'active' : ''}`;
        div.innerHTML = `<i class="fa-regular fa-message"></i> ${t.title || "New Chat"}`;
        div.onclick = () => loadConversation(t.id);
        historyList.appendChild(div);
    });
}

document.getElementById('new-chat-btn').onclick = () => {
    currentThreadId = generateUUID();
    localStorage.setItem('thread_id', currentThreadId);
    chatBox.innerHTML = '';
    document.getElementById('active-file-indicator').classList.add('hidden');
    loadThreads();
};

function generateUUID() { return crypto.randomUUID(); }
function scrollToBottom() { chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: 'smooth' }); }