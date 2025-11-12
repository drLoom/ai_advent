import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

app = Flask(__name__)

# OpenRouter API configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


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
        "model": "kwaipilot/kat-coder-pro:free",
        "temperature": 0.7 (optional, defaults to 0.7),
        "conversation_history": [] (optional, list of previous messages)
    }
    """
    if not OPENROUTER_API_KEY:
        return jsonify({
            "error": "OpenRouter API key not configured"
        }), 500

    try:
        # Parse request body
        data = request.get_json()

        if not data:
            return jsonify({
                "error": "Request body must be JSON"
            }), 400

        # Extract parameters
        user_message = data.get('message')
        model = data.get('model', 'kwaipilot/kat-coder-pro:free')
        temperature = data.get('temperature', 0.7)
        conversation_history = data.get('conversation_history', [])

        if not user_message:
            return jsonify({
                "error": "Missing required field: 'message'"
            }), 400

        # Build messages array for OpenAI
        messages = conversation_history.copy()
        messages.append({
            "role": "user",
            "content": user_message
        })

        # Prepare request to OpenRouter
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }

        # Forward request to OpenRouter
        response = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )

        # Check for errors from OpenRouter
        response.raise_for_status()

        # Extract response data
        response_data = response.json()
        ai_message = response_data["choices"][0]["message"]["content"]

        # Return formatted response
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

    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": f"Error communicating with OpenRouter: {str(e)}"
        }), 502

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
    if not OPENROUTER_API_KEY:
        print("❌ Error: OPENROUTER_API_KEY not found in environment variables.")
        print("Please create a .env file with your OpenRouter API key.")
        print("Get your API key from: https://openrouter.ai/keys")
        exit(1)

    print("🚀 Starting HTTP server...")
    print("📡 Server will forward requests to OpenRouter API")
    print("🔗 Health check: http://localhost:5000/health")
    print("💬 Chat endpoint: http://localhost:5000/chat (POST)")
    print("\nPress Ctrl+C to stop the server\n")

    app.run(host='0.0.0.0', port=3333, debug=True)
