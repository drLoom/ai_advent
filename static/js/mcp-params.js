// MCP Tool Parameters Handler
// Handles extraction and type conversion of MCP tool parameters from UI

class MCPToolParameters {
    constructor(toolName, tool) {
        this.toolName = toolName;
        this.tool = tool;
    }

    /**
     * Parse and extract tool parameters from UI inputs
     * @returns {Object} Tool arguments with proper type conversion
     */
    parse() {
        const props = this.tool.parameters?.properties || {};
        const toolArgs = {};

        for (const key of Object.keys(props)) {
            const input = document.getElementById(`param-${key}`);

            if (input && input.value) {
                const propType = props[key].type;
                toolArgs[key] = this.convertValue(input.value, propType);
            }
        }

        return toolArgs;
    }

    /**
     * Convert string value to appropriate type based on schema
     * @param {string} value - Raw input value
     * @param {string} type - Expected type from schema
     * @returns {*} Converted value
     */
    convertValue(value, type) {
        switch (type) {
            case 'number':
            case 'integer':
                return Number(value);
            case 'boolean':
                return value === 'true' || value === '1';
            case 'array':
                // Simple comma-separated array parsing
                return value.split(',').map(v => v.trim());
            default:
                return value;
        }
    }

    /**
     * Validate required parameters are present
     * @returns {Object} { valid: boolean, missing: Array<string> }
     */
    validate() {
        const required = this.tool.parameters?.required || [];
        const missing = [];

        for (const paramName of required) {
            const input = document.getElementById(`param-${paramName}`);
            if (!input || !input.value.trim()) {
                missing.push(paramName);
            }
        }

        return {
            valid: missing.length === 0,
            missing: missing
        };
    }

    /**
     * Build request body for MCP tool execution
     * @returns {Object} Request body for /mcp/call endpoint
     */
    toRequestBody() {
        return {
            tool_name: this.toolName,
            arguments: this.parse()
        };
    }
}


/**
 * Summarization Parameters Handler
 * Handles parameters specific to article summarization
 */
class SummarizationParameters {
    constructor() {
        this.temperatureInput = document.getElementById('temperature');
    }

    /**
     * Get temperature setting for summarization
     * @returns {number} Temperature value (default: 0.7)
     */
    getTemperature() {
        const value = parseFloat(this.temperatureInput?.value);
        return isNaN(value) ? 0.7 : value;
    }

    /**
     * Build request body for summarization endpoint
     * @param {string} content - Article content to summarize
     * @returns {Object} Request body for /summarize endpoint
     */
    toRequestBody(content) {
        return {
            content: content,
            temperature: this.getTemperature()
        };
    }
}
