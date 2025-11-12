## Requirements

- Python 3.10 or higher
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

   # For HTTP server (server.py)
   OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
   ```

   Get your API keys from:
   - OpenRouter: https://openrouter.ai/keys

## Usage

### Option 1: Interactive CLI (main.py)

Run the AI agent:

```bash
uv run main.py --message 'What is my name'
```

### Option 2: HTTP Server (server.py)

Run the HTTP server that accepts POST requests and forwards them to OpenRouter:

```bash
uv run server.py
```


The server will start on `http://localhost:3333`

**Endpoints:**

- `POST /chat` - Chat endpoint that forwards requests to OpenRouter API

**Example POST request to `/chat`:**

```bash
curl -X POST http://localhost:3333/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is my name",
    "conversation_history": [
      {"role": "user", "content": "Be short"}
    ]
  }'
```

**Request body parameters:**
- `message` (required): The user's message to send to the AI
  - Available models: `openai/gpt-4`, `anthropic/claude-3-opus`, `meta-llama/llama-3-70b`, etc.
  - See full list at: https://openrouter.ai/models
- `temperature` (optional): Response randomness, 0-2 (default: 0.7)
- `conversation_history` (optional): Array of previous messages to maintain context
- `short` (optional): Boolean. If set return only message from model

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
