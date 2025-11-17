import json
import logging
from ai.client import OpenRouterClient
from ai.models.research_response import ResearchResponse

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """
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


class Conversation:
    """Handles conversation logic and message processing."""

    def __init__(self, model: str, temperature: float = 0.7):
        """
        Initialize a conversation handler.

        Args:
            model: The model to use for completions
            temperature: Temperature parameter for the model (default: 0.7)
        """
        self.model = model
        self.temperature = temperature
        self.client = OpenRouterClient()

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
        logger.info(f"🆕 conversation history: {conversation_history}, research mode: {research}")

        # Build messages list
        messages = conversation_history.copy()

        # Add system prompt if in research mode
        if research:
            # If history is empty or doesn't have system prompt, add it at the beginning
            if not messages or messages[0].get("role") != "system":
                messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})

        messages.append({
            "role": "user",
            "content": user_message
        })

        response_format = ResearchResponse if research else None

        logger.info(f"request temperature: {self.temperature}, messages: {messages}")

        response_data = self.client.send_chat_completion(
            messages, model=self.model, temperature=self.temperature, response_format=response_format
        )

        logger.info(f"AI response data: {response_data}")

        ai_message = response_data["choices"][0]["message"]["content"]

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
            return {
                "success": True,
                "message": ai_message,
                "model": self.model,
                "usage": response_data.get("usage", {}),
                "conversation_history": messages + [{
                    "role": "assistant",
                    "content": ai_message
                }]
            }
