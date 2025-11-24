// Chat Parameters Handler
// Handles extraction and management of chat UI parameters

class ChatParameters {
    constructor() {
        this.messageInput = document.getElementById('messageInput');
        this.temperatureInput = document.getElementById('temperature');
        this.researchModeCheckbox = document.getElementById('researchMode');
        this.compressionEnabledCheckbox = document.getElementById('compressionEnabled');

        // Cache the message value immediately
        this.cachedMessage = this.messageInput?.value.trim() || '';
    }

    /**
     * Get the user's message text (returns cached value)
     * @returns {string} Trimmed message content
     */
    getMessage() {
        return this.cachedMessage;
    }

    /**
     * Get the temperature setting
     * @returns {number} Temperature value (default: 0.7)
     */
    getTemperature() {
        const value = parseFloat(this.temperatureInput?.value);
        return isNaN(value) ? 0.7 : value;
    }

    /**
     * Check if research mode is enabled
     * @returns {boolean}
     */
    isResearchMode() {
        return this.researchModeCheckbox?.checked || false;
    }

    /**
     * Check if history compression is enabled
     * @returns {boolean}
     */
    isCompressionEnabled() {
        return this.compressionEnabledCheckbox?.checked ?? true;
    }

    /**
     * Clear the message input
     */
    clearMessage() {
        if (this.messageInput) {
            this.messageInput.value = '';
            this.messageInput.style.height = 'auto';
        }
    }

    /**
     * Validate that required fields are present
     * @returns {boolean}
     */
    isValid() {
        return this.cachedMessage.length > 0;
    }

    /**
     * Build request body for chat endpoint
     * @param {Array} conversationHistory - Previous conversation messages
     * @returns {Object} Request body for /chat endpoint
     */
    toRequestBody(conversationHistory = []) {
        return {
            message: this.getMessage(),
            temperature: this.getTemperature(),
            conversation_history: conversationHistory,
            short: false,
            research: this.isResearchMode(),
            enable_compression: this.isCompressionEnabled()
        };
    }
}
