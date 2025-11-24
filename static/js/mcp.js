// MCP Tools Widget

let currentTools = [];

async function fetchMCPTools() {
    const toolsList = document.getElementById('mcpToolsList');
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');

    toolsList.innerHTML = '<div class="loading-tools">Loading...</div>';

    try {
        const response = await fetch('/mcp/tools');
        const data = await response.json();

        if (data.success) {
            // Update status
            if (data.connected) {
                statusDot.classList.add('connected');
                statusText.textContent = 'Connected';
            } else {
                statusDot.classList.remove('connected');
                statusText.textContent = 'Disconnected';
            }

            // Display tools
            if (data.tools && data.tools.length > 0) {
                currentTools = data.tools;
                toolsList.innerHTML = '';
                data.tools.forEach(tool => {
                    const toolItem = document.createElement('div');
                    toolItem.className = 'tool-item';
                    toolItem.onclick = () => showToolDialog(tool);

                    const toolName = document.createElement('div');
                    toolName.className = 'tool-name';
                    toolName.textContent = tool.name;

                    const toolDesc = document.createElement('div');
                    toolDesc.className = 'tool-description';
                    toolDesc.textContent = tool.description;

                    toolItem.appendChild(toolName);
                    toolItem.appendChild(toolDesc);
                    toolsList.appendChild(toolItem);
                });
            } else {
                toolsList.innerHTML = '<div class="loading-tools">No tools available</div>';
            }
        } else {
            toolsList.innerHTML = '<div class="loading-tools">Error loading tools</div>';
            statusDot.classList.remove('connected');
            statusText.textContent = 'Error';
        }
    } catch (error) {
        console.error('Failed to fetch MCP tools:', error);
        toolsList.innerHTML = '<div class="loading-tools">Connection failed</div>';
        statusDot.classList.remove('connected');
        statusText.textContent = 'Error';
    }
}

function showToolDialog(tool) {
    const dialog = document.createElement('div');
    dialog.className = 'tool-dialog-overlay';

    let paramsHTML = '';
    const props = tool.parameters?.properties || {};
    const required = tool.parameters?.required || [];

    for (const [key, value] of Object.entries(props)) {
        const isRequired = required.includes(key);
        paramsHTML += `
            <div class="param-field">
                <label>${key}${isRequired ? '*' : ''}</label>
                <input type="text" id="param-${key}" placeholder="${value.description || ''}" ${isRequired ? 'required' : ''}>
            </div>
        `;
    }

    dialog.innerHTML = `
        <div class="tool-dialog">
            <div class="tool-dialog-header">
                <h3>${tool.name}</h3>
                <button onclick="closeToolDialog()" class="close-btn">×</button>
            </div>
            <div class="tool-dialog-body">
                <p>${tool.description}</p>
                ${paramsHTML || '<p>No parameters required</p>'}
            </div>
            <div class="tool-dialog-footer">
                <button onclick="closeToolDialog()" class="cancel-btn">Cancel</button>
                <button onclick="executeTool('${tool.name}')" class="execute-btn">Execute</button>
            </div>
            <div id="toolResult" class="tool-result" style="display: none;"></div>
        </div>
    `;

    document.body.appendChild(dialog);
}

function closeToolDialog() {
    const dialog = document.querySelector('.tool-dialog-overlay');
    if (dialog) {
        dialog.remove();
    }
}

async function executeTool(toolName) {
    const tool = currentTools.find(t => t.name === toolName);

    // Use MCPToolParameters class to parse parameters
    const params = new MCPToolParameters(toolName, tool);

    // Validate required parameters
    const validation = params.validate();
    if (!validation.valid) {
        alert(`Missing required parameters: ${validation.missing.join(', ')}`);
        return;
    }

    const resultDiv = document.getElementById('toolResult');
    resultDiv.style.display = 'block';
    resultDiv.innerHTML = '<div class="loading-tools">Executing...</div>';

    try {
        const response = await fetch('/mcp/call', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(params.toRequestBody())
        });

        const data = await response.json();

        if (data.success) {
            resultDiv.innerHTML = `<pre>${data.result}</pre>`;

            // If it's fetch_article, automatically summarize with AI
            if (toolName === 'fetch_article') {
                resultDiv.innerHTML += '<div class="loading-tools" style="margin-top: 10px;">Summarizing with AI...</div>';

                // Send to backend for summarization
                await summarizeArticle(data.result, resultDiv);
            }
        } else {
            resultDiv.innerHTML = `<div class="error">Error: ${data.error}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="error">Failed to execute tool: ${error}</div>`;
    }
}

async function summarizeArticle(articleContent, resultDiv) {
    try {
        // Use SummarizationParameters class to build request
        const params = new SummarizationParameters();

        const response = await fetch('/summarize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(params.toRequestBody(articleContent))
        });

        const data = await response.json();

        if (data.success) {
            // Display summary in the tool result area
            resultDiv.innerHTML = `
                <div style="padding: 10px; background: #e7f3ff; border-left: 4px solid #2196F3; margin-bottom: 10px;">
                    <strong>AI Summary:</strong>
                </div>
                <pre style="white-space: pre-wrap;">${data.summary}</pre>
            `;
        } else {
            resultDiv.innerHTML += `<div class="error" style="margin-top: 10px;">Summarization error: ${data.error}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML += `<div class="error" style="margin-top: 10px;">Failed to summarize: ${error.message}</div>`;
    }
}

function refreshMCPTools() {
    fetchMCPTools();
}

// Load tools on page load
window.addEventListener('load', () => {
    fetchMCPTools();
});
