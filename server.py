import logging
from flask import Flask, request, jsonify, render_template
from conversation import Conversation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# MODEL = 'kwaipilot/kat-coder-pro:free'
# MODEL = 'google/gemini-2.5-flash-lite-preview-09-2025'
MODEL = 'nvidia/nemotron-nano-12b-v2-vl'
# MODEL = 'google/gemini-2.5-pro'

# Validator model - set to None to disable validation
VALIDATOR_MODEL = 'google/gemini-2.5-flash-lite-preview-09-2025'

# Transformer model - set to None to disable table transformation
TRANSFORMER_MODEL = 'google/gemini-2.5-pro'

app = Flask(__name__)


@app.route('/')
def index():
    """Render the chat UI."""
    return render_template('chat.html', model=MODEL)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "message": "Server is running"}), 200


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

        if not user_message:
            return jsonify({
                "error": "Missing required field: 'message'"
            }), 400

        conversation = Conversation(
            model=MODEL,
            temperature=temperature,
            validator_model=VALIDATOR_MODEL,
            transformer_model=TRANSFORMER_MODEL
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
