from flask import Flask, request, jsonify
from ai.client import OpenRouterClient

# Load environment variables

app = Flask(__name__)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "message": "Server is running"}), 200


@app.route('/chat', methods=['POST'])
def chat():
    """
    Accept POST requests and forward them to OpenRouter API.

    Expected request body:
    {
        "message": "Your message here",
        "temperature": 0.7 (optional, defaults to 0.7),
        "conversation_history": [] (optional, list of previous messages)
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "error": "Request body must be JSON"
            }), 400

        user_message = data.get('message')
        model = 'kwaipilot/kat-coder-pro:free'
        temperature = data.get('temperature', 0.7)
        conversation_history = data.get('conversation_history', [])
        short = data.get('short', False)

        if not user_message:
            return jsonify({
                "error": "Missing required field: 'message'"
            }), 400

        messages = conversation_history.copy()
        messages.append({
            "role": "user",
            "content": user_message
        })

        response_data = OpenRouterClient().send_chat_completion(messages, temperature=temperature)
        ai_message = response_data["choices"][0]["message"]["content"]
        ai_message = ai_message.split('\n')[0]
        if short:
            return jsonify({
                "success": True,
                "message": ai_message
            }), 200
        else:
            return jsonify({
                "success": True,
                "message": ai_message,
                "model": model,
                "usage": response_data.get("usage", {}),
                "conversation_history": messages + [{
                    "role": "assistant",
                    "content": ai_message
                }]
            }), 200

    except ValueError as e:
        return jsonify({
            "error": str(e)
        }), 500

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
