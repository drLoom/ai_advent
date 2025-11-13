import os
from openai import OpenAI

from dotenv import load_dotenv


class OpenAIClient:
    @classmethod
    def new(cls, api_key=None):
        load_dotenv()

        return OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )
