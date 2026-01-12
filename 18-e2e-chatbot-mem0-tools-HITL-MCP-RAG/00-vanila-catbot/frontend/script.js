const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const chatBox = document.getElementById('chat-box');

// Generate a random thread ID for this session
const threadId = "user_" + Math.random().toString(36).substr(2, 9);

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const message = userInput.value.trim();
    if (!message) return;

    // 1. Add User Message to UI
    appendMessage(message, 'user-message');
    userInput.value = '';

    // 2. Create a placeholder for AI Message
    const aiMessageContent = appendMessage('', 'ai-message');

    try {
        // 3. Send POST request to backend
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                message: message, 
                thread_id: threadId 
            })
        });

        // 4. Handle Streaming Response
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            // Decode the chunk and append to current AI bubble
            const chunk = decoder.decode(value);
            aiMessageContent.textContent += chunk;
            
            // Auto-scroll to bottom
            chatBox.scrollTop = chatBox.scrollHeight;
        }

    } catch (error) {
        console.error('Error:', error);
        aiMessageContent.textContent = "Error: Could not connect to server.";
    }
});

function appendMessage(text, className) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', className);

    const contentDiv = document.createElement('div');
    contentDiv.classList.add('content');
    contentDiv.textContent = text;

    messageDiv.appendChild(contentDiv);
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;

    return contentDiv; // Return reference to update text later
}