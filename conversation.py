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

    def __init__(self, model: str, temperature: float = 0.7, validator_model: str = None, transformer_model: str = None):
        """
        Initialize a conversation handler.

        Args:
            model: The model to use for completions
            temperature: Temperature parameter for the model (default: 0.7)
            validator_model: Optional model to validate responses (default: None)
            transformer_model: Optional model to transform response to table (default: None)
        """
        self.model = model
        self.temperature = temperature
        self.validator_model = validator_model
        self.transformer_model = transformer_model
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

        # Validate with second model if validator is configured
        validation_result = None
        if self.validator_model:
            validation_result = self._validate_response(
                user_message, ai_message
            )

        # Transform with third model if transformer is configured
        transformation_result = None
        if self.transformer_model:
            transformation_result = self._transform_to_table(
                user_message, ai_message
            )

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
                "usage": response_data.get("usage", {}),
                "conversation_history": messages + [{
                    "role": "assistant",
                    "content": ai_message
                }]
            }

            if validation_result:
                response["validation"] = validation_result

            if transformation_result:
                response["transformation"] = transformation_result

            return response

    def _validate_response(
        self, user_message: str, ai_response: str
    ) -> dict:
        """
        Validate AI response using validator model.

        Args:
            user_message: Original user message
            ai_response: AI generated response

        Returns:
            Dictionary containing validation results
        """
        validation_prompt = f"""You are a validator AI. Review this response:

User question: {user_message}

AI response: {ai_response}

Evaluate the response on:
FIND ERRORS
1. Accuracy - Is the information correct?
2. Completeness - Does it fully answer the question?
3. Clarity - Is it clear and well-structured?

Provide your evaluation in 2-3 sentences."""

        validation_messages = [
            {"role": "user", "content": validation_prompt}
        ]

        logger.info(f"Validating with model: {self.validator_model}")

        validation_data = self.client.send_chat_completion(
            validation_messages,
            model=self.validator_model,
            temperature=1.2
        )

        validation_message = validation_data["choices"][0]["message"]["content"]

        return {
            "message": validation_message,
            "model": self.validator_model,
            "usage": validation_data.get("usage", {})
        }

    def _transform_to_table(
        self, user_message: str, ai_response: str
    ) -> dict:
        """
        Transform AI response into table format using transformer model.

        Args:
            user_message: Original user message
            ai_response: AI generated response

        Returns:
            Dictionary containing transformed table
        """
        transformation_prompt = f"""Transform the following response into a well-structured HTML table format.

User question: {user_message}

AI response: {ai_response}

Create an HTML table that organizes the key information from the response. Use proper table structure with <table>, <thead>, <tbody>, <tr>, <th>, and <td> tags. Make it clear and easy to read. Only output the HTML table, nothing else."""

        transformation_messages = [
            {"role": "user", "content": transformation_prompt}
        ]

        logger.info(f"Transforming with model: {self.transformer_model}")

        transformation_data = self.client.send_chat_completion(
            transformation_messages,
            model=self.transformer_model,
            temperature=0.3
        )

        transformation_message = transformation_data["choices"][0]["message"]["content"]

        return {
            "message": transformation_message,
            "model": self.transformer_model,
            "usage": transformation_data.get("usage", {})
        }
