import logging
from flask import Flask, request, jsonify, render_template
from conversation import Conversation
from mcp_client import MCPClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# MODEL = 'kwaipilot/kat-coder-pro:free'
# MODEL = 'google/gemini-2.5-flash-lite-preview-09-2025'
MODEL = 'nvidia/nemotron-nano-12b-v2-vl'
# MODEL = 'google/gemini-2.5-pro'

app = Flask(__name__)

# Initialize MCP client (default: filesystem, change to mcp_server_news.py for news)
mcp_client = MCPClient("mcp_server_news.py")


@app.route('/')
def index():
    """Render the chat UI."""
    return render_template('chat.html', model=MODEL)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "message": "Server is running"}), 200


@app.route('/mcp/tools', methods=['GET'])
def get_mcp_tools():
    """Get available MCP tools."""
    try:
        # Connect if not already connected
        if not mcp_client.connected:
            mcp_client.connect()

        tools = mcp_client.get_tools()
        return jsonify({
            "success": True,
            "connected": mcp_client.connected,
            "tools": tools
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/mcp/call', methods=['POST'])
def call_mcp_tool():
    """Call an MCP tool."""
    try:
        data = request.get_json()
        tool_name = data.get('tool_name')
        arguments = data.get('arguments', {})

        if not tool_name:
            return jsonify({
                "success": False,
                "error": "Missing tool_name"
            }), 400

        # Connect if not already connected
        if not mcp_client.connected:
            mcp_client.connect()

        result = mcp_client.call_tool(tool_name, arguments)
        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/summarize', methods=['POST'])
def summarize_article():
    """Summarize article content using AI."""
    try:
        data = request.get_json()
        article_content = data.get('content')
        temperature = data.get('temperature', 0.7)

        if not article_content:
            return jsonify({
                "success": False,
                "error": "Missing article content"
            }), 400

        # Create conversation instance
        conversation = Conversation(
            model=MODEL,
            temperature=temperature,
            enable_compression=False  # No history for single summarization
        )

        # Process summarization request
        response = conversation.process_message(
            user_message=f"""Please provide a well-structured, concise summary of this article.

Format your response as:
1. Main Points (3-5 bullet points)
2. Brief Summary (2-3 sentences)

Article content:
{article_content}""",
            conversation_history=[],
            short=False,
            research=False
        )

        if response.get('error'):
            return jsonify({
                "success": False,
                "error": response['error']
            }), 500

        return jsonify({
            "success": True,
            "summary": response['message']
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "error": "Request body must be JSON"
            }), 400

        user_message = data.get('message')
        temperature = data.get('temperature', 0.7)
        conversation_history = data.get('conversation_history', [])
        short = data.get('short', False)
        research = data.get('research', False)
        enable_compression = data.get('enable_compression', True)

        if not user_message:
            return jsonify({
                "error": "Missing required field: 'message'"
            }), 400

        conversation = Conversation(
            model=MODEL,
            temperature=temperature,
            enable_compression=enable_compression
        )
        response = conversation.process_message(
            user_message=user_message,
            conversation_history=conversation_history,
            short=short,
            research=research
        )

        return jsonify(response), 200

    except Exception as e:
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        "error": "Endpoint not found"
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    return jsonify({
        "error": "Method not allowed"
    }), 405


if __name__ == '__main__':
    print("🚀 Starting HTTP server...")
    print("📡 Server will forward requests to OpenRouter API")
    print("🔗 Health check: http://localhost:3333/health")
    print("💬 Chat endpoint: http://localhost:3333/chat (POST)")
    print("\nPress Ctrl+C to stop the server\n")

    app.run(host='0.0.0.0', port=3333, debug=True)
