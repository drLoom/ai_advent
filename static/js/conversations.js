let currentConversationId = null;

async function loadConversations() {
    try {
        const response = await fetch('/conversations?limit=50');
        const data = await response.json();

        const conversationsList = document.getElementById('conversationsList');

        if (!data.success || !data.conversations || data.conversations.length === 0) {
            conversationsList.innerHTML = '<div class="no-conversations">No conversations yet</div>';
            return;
        }

        conversationsList.innerHTML = '';

        data.conversations.forEach(conv => {
            const convElement = document.createElement('div');
            convElement.className = 'conversation-item';
            if (conv.id === currentConversationId) {
                convElement.classList.add('active');
            }

            const createdDate = new Date(conv.created_at);
            const updatedDate = new Date(conv.updated_at);
            const timeStr = formatRelativeTime(updatedDate);
            const fullTimestamp = formatFullTimestamp(createdDate);

            convElement.innerHTML = `
                <div class="conversation-info">
                    <div class="conversation-message-count">${conv.message_count} messages (ID: ${conv.id})</div>
                    <div class="conversation-time">${fullTimestamp}</div>
                </div>
            `;

            convElement.onclick = () => loadConversation(conv.id);
            conversationsList.appendChild(convElement);
        });
    } catch (error) {
        console.error('Error loading conversations:', error);
        document.getElementById('conversationsList').innerHTML = '<div class="error-conversations">Failed to load</div>';
    }
}

async function loadConversation(conversationId) {
    try {
        const response = await fetch(`/conversations/${conversationId}`);
        const data = await response.json();

        if (!data.success || !data.conversation) {
            console.error('Failed to load conversation');
            return;
        }

        currentConversationId = conversationId;

        const chatMessages = document.getElementById('chatMessages');
        chatMessages.innerHTML = '';

        if (data.conversation.messages && data.conversation.messages.length > 0) {
            data.conversation.messages.forEach(msg => {
                addMessage(msg.role, msg.content, null, null, msg.created_at);
            });
        }

        conversationHistory = data.conversation.messages.map(msg => ({
            role: msg.role,
            content: msg.content
        }));

        loadConversations();

        chatMessages.scrollTop = chatMessages.scrollHeight;
    } catch (error) {
        console.error('Error loading conversation:', error);
    }
}

function newConversation() {
    currentConversationId = null;
    conversationHistory = [];

    const chatMessages = document.getElementById('chatMessages');
    chatMessages.innerHTML = `
        <div class="message assistant">
            <div class="message-content">
                Hello! I'm your AI assistant. How can I help you today?
            </div>
        </div>
    `;

    loadConversations();
}

function formatRelativeTime(date) {
    const now = new Date();
    const diff = now - date;
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (seconds < 60) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;

    return date.toLocaleDateString();
}

function formatFullTimestamp(date) {
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatMessageTime(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

document.addEventListener('DOMContentLoaded', () => {
    loadConversations();
});
