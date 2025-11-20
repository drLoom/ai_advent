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
uv run main.py parse_review --review "Love the new update! Dark mode looks great. But please fix the crash on iOS 18. 5 stars."
```

### Option 2: HTTP Server (server.py)

Run the HTTP server that accepts POST requests and forwards them to OpenRouter:

```bash
uv run server.py
```
