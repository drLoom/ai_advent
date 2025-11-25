import json
import logging
from typing import Optional, List, Dict
from ai.client import OpenRouterClient
from ai.models.research_response import ResearchResponse
from ai.history_compressor import HistoryCompressor

logger = logging.getLogger(__name__)


RESEARCH_SYSTEM_PROMPT = """
You collect requirements for a project specification.

You must ALWAYS respond in **one** of the Pydantic formats below:

1. ContinueResponse:
{
  "status": "continue",
  "question": "<ask your next question>",
  "notes": "<summarize what you know so far>"
}

2. FinalResponse:
{
  "status": "final",
  "result": "<the finished specification>"
}

RULES:
- Switch to status="final" ONLY when you are certain all required info is complete.
- Never output anything outside JSON.
- Never mix fields from both models.
"""

TOOL_SYSTEM_PROMPT = """
You are a helpful AI assistant with access to tools for fetching and analyzing news articles.

Available tools:
- fetch_article: Fetches full content of a single article from a URL
- fetch_multiple_articles: Fetches a list of article links from a news category or listing page

When users ask you to:
- Summarize articles from a website → Use fetch_multiple_articles to get article links, then fetch_article for each one
- Get latest news from a site → Use fetch_multiple_articles on the site's category page
- Fetch/read/analyze an article → Use fetch_article with the URL

Always use tools when you need current information from websites. Don't make up or guess article content.
"""


class Conversation:
    """Handles conversation logic and message processing."""

    def __init__(
        self,
        model: str,
        temperature: float = 0.7,
        enable_compression: bool = True,
        compression_threshold: int = 10,
        keep_recent: int = 2,
        mcp_client=None
    ):
        """
        Initialize a conversation handler.

        Args:
            model: The model to use for completions
            temperature: Temperature parameter for the model (default: 0.7)
            enable_compression: Enable history compression (default: True)
            compression_threshold: Number of messages before compression (default: 10)
            keep_recent: Number of recent messages to keep uncompressed (default: 4)
            mcp_client: Optional MCP client for tool calling
        """
        self.model = model
        self.temperature = temperature
        self.client = OpenRouterClient()
        self.mcp_client = mcp_client

        # Initialize history compressor
        self.enable_compression = enable_compression
        if enable_compression:
            self.compressor = HistoryCompressor(
                client=self.client,
                compression_threshold=compression_threshold,
                keep_recent=keep_recent
            )
        else:
            self.compressor = None

    def _convert_mcp_tools_to_openrouter_format(self, mcp_tools: List[Dict]) -> List[Dict]:
        """
        Convert MCP tool definitions to OpenRouter function calling format.

        Args:
            mcp_tools: List of MCP tool definitions

        Returns:
            List of tools in OpenRouter format
        """
        openrouter_tools = []
        for tool in mcp_tools:
            openrouter_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"]
                }
            })
        return openrouter_tools

    def process_message(
        self,
        user_message: str,
        conversation_history: list = None,
        short: bool = False,
        research: bool = False
    ) -> dict:
        """
        Process a user message and get AI response.

        Args:
            user_message: The user's message
            conversation_history: Previous conversation messages (default: empty list)
            short: If True, return only the message without metadata
            research: If True, enable research mode

        Returns:
            Dictionary containing the response data
        """
        if conversation_history is None:
            conversation_history = []
        logger.info(f"conversation history: {conversation_history}, research mode: {research}")

        # Check if compression is needed and apply it
        compression_metrics = None
        if self.enable_compression and self.compressor: #and self.compressor.should_compress(conversation_history):
            logger.info("Triggering history compression...")
            conversation_history, compression_metrics = self.compressor.compress_history(conversation_history)
            logger.info(f"Compression complete. Metrics: {compression_metrics}")

        # Build messages list
        messages = conversation_history.copy()

        # Add system prompt based on mode
        if not messages or messages[0].get("role") != "system":
            if research:
                # Research mode: structured output for requirements gathering
                messages.insert(0, {"role": "system", "content": RESEARCH_SYSTEM_PROMPT})
            elif self.mcp_client and self.mcp_client.connected:
                # Tool mode: guide the AI to use available tools
                messages.insert(0, {"role": "system", "content": TOOL_SYSTEM_PROMPT})

        messages.append({
            "role": "user",
            "content": user_message
        })

        # Get MCP tools if available (but not in research mode, as it conflicts with response_format)
        tools = None
        if not research and self.mcp_client and self.mcp_client.connected:
            try:
                mcp_tools = self.mcp_client.get_tools()
                if mcp_tools:
                    tools = self._convert_mcp_tools_to_openrouter_format(mcp_tools)
                    logger.info(f"Loaded {len(tools)} tools for AI")
            except Exception as e:
                logger.error(f"Failed to get MCP tools: {e}")

        response_format = ResearchResponse if research else None

        # Tool calling loop - continue until no more tool calls
        max_iterations = 10
        iteration = 0
        total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        while iteration < max_iterations:
            iteration += 1
            logger.info(f"Tool calling iteration {iteration}/{max_iterations}")
            logger.info(f"request temperature: {self.temperature}, messages count: {len(messages)}")

            response_data = self.client.send_chat_completion(
                messages,
                model=self.model,
                temperature=self.temperature,
                response_format=response_format,
                tools=tools
            )

            logger.info(f"AI response data: {response_data}")

            # Accumulate usage stats
            if "usage" in response_data:
                for key in ["prompt_tokens", "completion_tokens", "total_tokens"]:
                    total_usage[key] += response_data["usage"].get(key, 0)

            message = response_data["choices"][0]["message"]

            # Check if the model wants to call tools
            tool_calls = message.get("tool_calls")

            if tool_calls:
                logger.info(f"Model requested {len(tool_calls)} tool calls")

                # Add assistant message with tool calls to history
                messages.append({
                    "role": "assistant",
                    "content": message.get("content") or "",
                    "tool_calls": tool_calls
                })

                # Execute each tool call
                for tool_call in tool_calls:
                    tool_name = tool_call["function"]["name"]
                    tool_args = json.loads(tool_call["function"]["arguments"])
                    tool_id = tool_call["id"]

                    logger.info(f"Executing tool: {tool_name} with args: {tool_args}")

                    # Call the MCP tool
                    tool_result = self.mcp_client.call_tool(tool_name, tool_args)

                    # Extract the actual result string from the MCP response
                    if tool_result.get("success") and "result" in tool_result:
                        result_content = tool_result["result"]
                    else:
                        result_content = json.dumps(tool_result)

                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "content": result_content
                    })

                # Continue loop to get next response
                continue
            else:
                # No tool calls, we have the final response
                ai_message = message.get("content", "")

                if research:
                    data = json.loads(ai_message)
                    if data["status"] == "final":
                        ai_message = data["result"]
                    else:
                        ai_message = data["question"]

                # Build response based on short flag
                if short:
                    return {
                        "success": True,
                        "message": ai_message
                    }
                else:
                    response = {
                        "success": True,
                        "message": ai_message,
                        "model": self.model,
                        "usage": total_usage,
                        "conversation_history": messages + [{
                            "role": "assistant",
                            "content": ai_message
                        }]
                    }

                    if compression_metrics:
                        response["compression"] = compression_metrics

                    return response

        # Max iterations reached
        logger.warning(f"Max tool calling iterations ({max_iterations}) reached")
        return {
            "success": False,
            "error": "Max tool calling iterations reached",
            "message": "I apologize, but I encountered too many tool calls and need to stop."
        }
