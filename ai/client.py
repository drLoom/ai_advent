import os
import requests
from dotenv import load_dotenv


class OpenRouterClient:
    """Client for interacting with OpenRouter API."""

    URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_key=None):
        """
        Initialize the OpenRouter client.

        Args:
            api_key: Optional API key. If not provided, loads from environment.

        Raises:
            ValueError: If API key is not configured
        """

        load_dotenv()

        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OpenRouter API key not configured")

    def default_headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def send_chat_completion(
        self, messages, model="kwaipilot/kat-coder-pro:free", temperature=0.7, response_format=None
    ):
        """
        Send a chat completion request to OpenRouter API.

        Args:
            messages: List of message objects with 'role' and 'content' keys
            model: Model to use for completion
            temperature: Temperature parameter for response generation
            response_format: Optional response format schema (Pydantic model)

        Returns:
            dict: Response data from OpenRouter API

        Raises:
            requests.exceptions.RequestException: If request fails
        """
        headers = self.default_headers()
        payload = {"model": model, "messages": messages, "temperature": temperature}

        # Add response_format if provided
        if response_format:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": response_format.__name__,
                    "schema": response_format.model_json_schema(),
                    "strict": True
                }
            }

        response = requests.post(self.URL, headers=headers, json=payload, timeout=30)

        response.raise_for_status()
        response_data = response.json()

        return response_data
