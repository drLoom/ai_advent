# Simple AI Agent

A simple AI agent that accepts user input, makes HTTP requests to an AI model (OpenAI), and displays responses in an interactive command-line interface.

## Features

- 🤖 Interactive chat interface with AI
- 💬 Maintains conversation history
- 🔄 HTTP client-based communication with OpenAI API
- ⚡ Simple and clean command-line interface
- 🧹 Clear conversation history on demand

## Requirements

- Python 3.10 or higher
- OpenAI API key (for interactive CLI)
- OpenRouter API key (for HTTP server)

## Installation

1. **Clone or navigate to the project directory**

2. **Install dependencies using uv:**
   ```bash
   uv sync
   ```

3. **Set up your API keys:**

   Create a `.env` file in the project root:
   ```bash
   cp .env.example .env
   ```

   Then edit `.env` and add your API keys:
   ```
   # For interactive CLI (main.py)
   OPENAI_API_KEY=sk-your-actual-api-key-here

   # For HTTP server (server.py)
   OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
   ```

   Get your API keys from:
   - OpenAI: https://platform.openai.com/api-keys
   - OpenRouter: https://openrouter.ai/keys

## Usage

### Option 1: Interactive CLI (main.py)

Run the AI agent:

```bash
uv run main.py
```

Or with Python directly:

```bash
python main.py
```

**Commands:**
- Type your question and press Enter to chat with the AI
- Type `clear` to clear conversation history
- Type `quit` or `exit` to exit the program
- Press `Ctrl+C` to force quit

### Option 2: HTTP Server (server.py)

Run the HTTP server that accepts POST requests and forwards them to OpenRouter:

```bash
uv run server.py
```


The server will start on `http://localhost:3333`

**Endpoints:**

- `GET /health` - Health check endpoint
- `POST /chat` - Chat endpoint that forwards requests to OpenRouter API

**Example POST request to `/chat`:**

```bash
curl -X POST http://localhost:3333/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the capital of France?",
    "model": "openai/gpt-3.5-turbo",
    "temperature": 0.7
  }'
```

**Request body parameters:**
- `message` (required): The user's message to send to the AI
- `model` (optional): Model to use via OpenRouter (default: "openai/gpt-3.5-turbo")
  - Available models: `openai/gpt-4`, `anthropic/claude-3-opus`, `meta-llama/llama-3-70b`, etc.
  - See full list at: https://openrouter.ai/models
- `temperature` (optional): Response randomness, 0-2 (default: 0.7)
- `conversation_history` (optional): Array of previous messages to maintain context

**Example with conversation history:**

```bash
curl -X POST http://localhost:3333/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me more about it",
    "conversation_history": [
      {"role": "user", "content": "What is the capital of France?"},
      {"role": "assistant", "content": "The capital of France is Paris."}
    ]
  }'
```

**Response format:**

```json
{
  "success": true,
  "message": "The capital of France is Paris.",
  "model": "openai/gpt-3.5-turbo",
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 8,
    "total_tokens": 20
  },
  "conversation_history": [
    {"role": "user", "content": "What is the capital of France?"},
    {"role": "assistant", "content": "The capital of France is Paris."}
  ]
}
```

**Why OpenRouter?**

OpenRouter provides access to multiple AI models through a single API:
- Access GPT-4, Claude, Llama, and many other models
- Unified API format across all providers
- Pay-as-you-go pricing with credits
- Automatic failover and model routing
- No need to manage multiple API keys from different providers

### Example Session

```
============================================================
🤖 Simple AI Agent - Interactive Chat Interface
============================================================

Commands:
  - Type your question and press Enter to chat
  - Type 'clear' to clear conversation history
  - Type 'quit' or 'exit' to exit the program

============================================================

💬 You: What is the capital of France?

🤖 AI Agent:
------------------------------------------------------------
The capital of France is Paris.
------------------------------------------------------------

💬 You: Tell me an interesting fact about it.

🤖 AI Agent:
------------------------------------------------------------
Paris is known as the "City of Light" (La Ville Lumière),
not because of its romantic ambiance, but because it was
one of the first European cities to use gas street lighting
extensively in the 19th century.
------------------------------------------------------------

💬 You: quit

👋 Goodbye! Thanks for chatting.
```

## How It Works

1. **User Input**: The agent accepts input from the command line
2. **HTTP Request**: Sends the input to OpenAI's API using the `requests` library
3. **API Processing**: OpenAI processes the request and generates a response
4. **HTTP Response**: The agent receives the response via HTTP
5. **Display**: The response is formatted and displayed to the user
6. **Conversation History**: All messages are stored to maintain context

## Project Structure

```
.
├── main.py           # Interactive CLI AI agent
├── server.py         # HTTP server that forwards requests to OpenAI
├── pyproject.toml    # Project dependencies and configuration
├── .env.example      # Example environment variables file
├── .env              # Your API keys (not in git)
└── README.md         # This file
```

## Technical Details

- **HTTP Client**: Uses `requests` library for HTTP communication
- **Web Framework**: Uses `Flask` for the HTTP server
- **Interactive CLI**: OpenAI Chat Completions API (GPT-3.5-turbo by default)
- **HTTP Server**: OpenRouter API (supports multiple models)
- **Environment Management**: Uses `python-dotenv` for secure API key storage
- **Conversation Memory**: Maintains full conversation history for context

## Troubleshooting

**Error: OPENAI_API_KEY not found (main.py)**
- Make sure you created a `.env` file with your OpenAI API key
- Check that the key is properly formatted: `OPENAI_API_KEY=sk-...`

**Error: OPENROUTER_API_KEY not found (server.py)**
- Make sure you created a `.env` file with your OpenRouter API key
- Check that the key is properly formatted: `OPENROUTER_API_KEY=sk-or-v1-...`
- Get your key from: https://openrouter.ai/keys

**HTTP Request Errors**
- Verify your API key is valid and active
- Check your internet connection
- Ensure you have available API credits on your account

## License

This is a sample project for learning purposes.
