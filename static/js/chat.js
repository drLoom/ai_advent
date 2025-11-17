let conversationHistory = [];
let temperature = 0.7;

// Auto-resize textarea
const messageInput = document.getElementById('messageInput');
messageInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
});

// Send message on Enter (Shift+Enter for new line)
messageInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

function updateTemp(value) {
    temperature = parseFloat(value);
    document.getElementById('tempValue').textContent = value;
}

function addMessage(role, content, responseTime = null) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const label = role === 'user' ? 'You' : 'AI';
    // Preserve newlines by replacing them with <br>
    const formattedContent = escapeHtml(content).replace(/\n/g, '<br>');
    contentDiv.innerHTML = `<strong>${label}:</strong> ${formattedContent}`;

    messageDiv.appendChild(contentDiv);

    // Add response time indicator if provided
    if (responseTime !== null && role === 'assistant') {
        const timeDiv = document.createElement('div');
        timeDiv.className = 'response-time';
        timeDiv.textContent = `${responseTime}ms`;
        messageDiv.appendChild(timeDiv);
    }

    chatMessages.appendChild(messageDiv);

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showTypingIndicator() {
    const chatMessages = document.getElementById('chatMessages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message assistant';
    typingDiv.id = 'typing-indicator';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content typing-indicator';
    contentDiv.innerHTML = '<span class="loading"></span><span class="loading"></span><span class="loading"></span>';

    typingDiv.appendChild(contentDiv);
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

async function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    const message = messageInput.value.trim();

    if (!message) return;

    // Disable input
    messageInput.disabled = true;
    sendButton.disabled = true;

    // Add user message to UI
    addMessage('user', message);

    // Clear input
    messageInput.value = '';
    messageInput.style.height = 'auto';

    // Show typing indicator
    showTypingIndicator();

    // Track request start time
    const startTime = performance.now();

    try {
        const researchMode = document.getElementById('researchMode').checked;
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                temperature: temperature,
                conversation_history: conversationHistory,
                research: researchMode
            })
        });

        const data = await response.json();

        // Calculate response time
        const endTime = performance.now();
        const responseTime = Math.round(endTime - startTime);

        // Remove typing indicator
        removeTypingIndicator();

        if (data.success) {
            // Parse and format research mode responses
            let displayMessage = data.message;
            try {
                const parsed = JSON.parse(data.message);
                if (parsed.status) {
                    // Format research response nicely
                    displayMessage = `Status: ${parsed.status}\n`;
                    if (parsed.question) displayMessage += `Question: ${parsed.question}\n`;
                    if (parsed.notes) displayMessage += `Notes: ${parsed.notes}\n`;
                    if (parsed.result) displayMessage += `Result: ${parsed.result}`;
                }
            } catch (e) {
                // Not JSON, use message as-is
            }

            // Add AI response to UI with response time
            addMessage('assistant', displayMessage, responseTime);

            // Update conversation history
            conversationHistory = data.conversation_history;
        } else {
            addMessage('assistant', 'Error: ' + (data.error || 'Unknown error occurred'));
        }
    } catch (error) {
        removeTypingIndicator();
        addMessage('assistant', 'Error: Failed to connect to server');
        console.error('Error:', error);
    } finally {
        // Re-enable input
        messageInput.disabled = false;
        sendButton.disabled = false;
        messageInput.focus();
    }
}

function clearChat() {
    if (confirm('Are you sure you want to clear the chat?')) {
        conversationHistory = [];
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.innerHTML = `
            <div class="message assistant">
                <div class="message-content">
                    <strong>AI:</strong> Hello! I'm your AI assistant. How can I help you today?
                </div>
            </div>
        `;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Focus input on load
window.addEventListener('load', () => {
    messageInput.focus();
});
