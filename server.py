import logging
import os
import base64
import requests
import tempfile
from flask import Flask, request, jsonify, render_template
from pydub import AudioSegment
from conversation import Conversation
from servers.client_manager import MCPClientManager
from storage import ArticleStorage
from params import (
    ChatRequestParams,
    MCPToolRequestParams,
    SummarizationRequestParams,
    ValidationError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# MODEL = 'kwaipilot/kat-coder-pro:free'
# Use Gemini model for tool calling support
MODEL = 'google/gemini-2.5-flash-lite-preview-09-2025'
# MODEL = 'nvidia/nemotron-nano-12b-v2-vl'  # Doesn't support function calling
# MODEL = 'google/gemini-2.5-pro'

# Research mode requires structured outputs - use a model that supports it
RESEARCH_MODEL = 'google/gemini-2.5-flash-lite-preview-09-2025'

app = Flask(__name__)

# Initialize MCP client manager with all servers
mcp_client = MCPClientManager([
    "servers/server_news.py",
    "servers/server_articles.py",
    "servers/server_reviews.py",
    "servers/server_filesystem.py"
])

# Initialize storage for conversation logging
storage = ArticleStorage()

# OpenRouter API configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


@app.route('/')
def index():
    """Render the chat UI."""
    return render_template(
        'chat.html', model=MODEL, research_model=RESEARCH_MODEL
    )


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
        # Use MCPToolRequestParams to parse and validate request
        params = MCPToolRequestParams.from_request(request.get_json())

        # Connect if not already connected
        if not mcp_client.connected:
            mcp_client.connect()

        # Execute tool with validated parameters
        result = mcp_client.call_tool(params.tool_name, params.arguments)
        return jsonify(result), 200

    except ValidationError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/summarize', methods=['POST'])
def summarize_article():
    """Summarize article content using AI."""
    try:
        # Use SummarizationRequestParams to parse and validate request
        params = SummarizationRequestParams.from_request(request.get_json())

        # Create conversation instance
        conversation = Conversation(
            model=MODEL,
            temperature=params.temperature,
            enable_compression=False  # No history for single summarization
        )

        # Process summarization request
        response = conversation.process_message(
            user_message=f"""Please provide a well-structured, \
concise summary of this article.

Format your response as:
1. Main Points (3-5 bullet points)
2. Brief Summary (2-3 sentences)

Article content:
{params.content}""",
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

    except ValidationError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/conversations', methods=['GET'])
def get_conversations():
    """Get list of all conversations."""
    try:
        limit = request.args.get('limit', type=int)
        conversations = storage.list_conversations(limit=limit)
        return jsonify({
            "success": True,
            "conversations": conversations
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/conversations/<int:conversation_id>', methods=['GET'])
def get_conversation(conversation_id: int):
    """Get a specific conversation with all messages."""
    try:
        conversation = storage.get_conversation_with_messages(conversation_id)

        if not conversation:
            return jsonify({
                "success": False,
                "error": f"Conversation {conversation_id} not found"
            }), 404

        return jsonify({
            "success": True,
            "conversation": conversation
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/chat', methods=['POST'])
def chat():
    try:
        # Use ChatRequestParams to parse and validate request
        params = ChatRequestParams.from_request(request.get_json())

        # Use RESEARCH_MODEL for research mode (supports structured outputs)
        # Otherwise use regular MODEL
        selected_model = RESEARCH_MODEL if params.research else MODEL

        # Connect to MCP server if not already connected
        if not mcp_client.connected:
            mcp_client.connect()

        # Create or retrieve conversation for logging
        if params.conversation_id:
            conversation_id = params.conversation_id
        else:
            conversation_id = storage.create_conversation()

        # Log user message
        storage.save_message(
            conversation_id=conversation_id,
            role="user",
            content=params.message
        )

        # Create conversation with validated parameters and MCP client
        conversation = Conversation(
            model=selected_model,
            temperature=params.temperature,
            enable_compression=params.enable_compression,
            mcp_client=mcp_client
        )

        # Process message
        response = conversation.process_message(
            user_message=params.message,
            conversation_history=params.conversation_history,
            short=params.short,
            research=params.research
        )

        # Log assistant response if successful
        if not response.get('error'):
            storage.save_message(
                conversation_id=conversation_id,
                role="assistant",
                content=response.get('message', ''),
                model_name=selected_model,
                prompt_tokens=response.get('prompt_tokens'),
                completion_tokens=response.get('completion_tokens'),
                total_tokens=response.get('total_tokens'),
                temperature=params.temperature
            )

        # Add conversation_id to response
        response['conversation_id'] = conversation_id

        return jsonify(response), 200

    except ValidationError as e:
        return jsonify({
            "error": str(e)
        }), 400

    except Exception as e:
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    """Transcribe audio using OpenRouter multimodal API."""
    temp_webm_path = None
    temp_wav_path = None

    try:
        # Check if audio file is present
        if 'audio' not in request.files:
            return jsonify({
                "success": False,
                "error": "No audio file provided"
            }), 400

        audio_file = request.files['audio']

        if audio_file.filename == '':
            return jsonify({
                "success": False,
                "error": "Empty filename"
            }), 400

        # Save uploaded WebM file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_webm:
            audio_file.save(temp_webm.name)
            temp_webm_path = temp_webm.name

        # Convert WebM to WAV using pydub
        audio = AudioSegment.from_file(temp_webm_path, format="webm")

        # Create temporary WAV file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_wav:
            temp_wav_path = temp_wav.name

        # Export as WAV
        audio.export(temp_wav_path, format="wav")

        # Read WAV file and encode to base64
        with open(temp_wav_path, 'rb') as wav_file:
            audio_data = wav_file.read()
            base64_audio = base64.b64encode(audio_data).decode('utf-8')

        # Prepare OpenRouter API request
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "google/gemini-2.5-flash",  # Free model with audio support
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please transcribe this audio file. Only return the transcribed text, nothing else."
                        },
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": base64_audio,
                                "format": "wav"
                            }
                        }
                    ]
                }
            ]
        }

        # Call OpenRouter API
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload)
        response.raise_for_status()

        result = response.json()

        transcript = result.get('choices', [{}])[0].get('message', {}).get('content', '')


        logging.info(f"Transcription result: {transcript}  ")



        # conversation = Conversation(
        #     model=MODEL,
        #     temperature=0.7,
        #     enable_compression=False
        # )


        # # Process message
        # response = conversation.process_message(
        #     user_message=transcript,
        # )


        return jsonify({
            "success": True,
            "text": transcript
        }), 200

    except Exception as e:
        logging.error(f"Transcription error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

    finally:
        # Clean up temporary files
        if temp_webm_path and os.path.exists(temp_webm_path):
            os.unlink(temp_webm_path)
        if temp_wav_path and os.path.exists(temp_wav_path):
            os.unlink(temp_wav_path)



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
    print(f"🤖 Default model: {MODEL}")
    print(f"🔬 Research model: {RESEARCH_MODEL}")
    print("🔗 Health check: http://localhost:3333/health")
    print("💬 Chat endpoint: http://localhost:3333/chat (POST)")
    print("\nPress Ctrl+C to stop the server\n")

    app.run(host='0.0.0.0', port=3333, debug=True)
