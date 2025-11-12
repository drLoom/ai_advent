import os
import sys

import requests
from dotenv import load_dotenv


class AIAgent:
    """Simple AI agent that uses HTTP client to communicate with OpenAI API."""

    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.conversation_history = []

    def send_message(self, user_message: str) -> str:
        """Send a message to the AI model via HTTP request and return the response."""
        # Add user message to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Prepare the HTTP request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": self.model,
            "messages": self.conversation_history,
            "temperature": 0.7
        }

        try:
            # Make HTTP POST request
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )

            # Check for errors
            response.raise_for_status()

            # Extract the AI's response
            data = response.json()
            ai_message = data["choices"][0]["message"]["content"]

            # Add AI response to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": ai_message
            })

            return ai_message

        except requests.exceptions.RequestException as e:
            return f"Error communicating with AI: {str(e)}"

    def clear_history(self):
        """Clear the conversation history."""
        self.conversation_history = []


def display_welcome():
    """Display welcome message and instructions."""
    print("=" * 60)
    print("🤖 Simple AI Agent - Interactive Chat Interface")
    print("=" * 60)
    print("\nCommands:")
    print("  - Type your question and press Enter to chat")
    print("  - Type 'clear' to clear conversation history")
    print("  - Type 'quit' or 'exit' to exit the program")
    print("\n" + "=" * 60 + "\n")


def display_response(response: str):
    """Display the AI's response in a formatted way."""
    print("\n🤖 AI Agent:")
    print("-" * 60)
    print(response)
    print("-" * 60 + "\n")


def main():
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables.")
        sys.exit(1)

    agent = AIAgent(api_key)

    display_welcome()

    while True:
        try:
            # Get user input
            user_input = input("💬 You: ").strip()

            # Check for exit commands
            if user_input.lower() in ['quit', 'exit']:
                print("\n👋 Goodbye! Thanks for chatting.")
                break

            # Check for clear command
            if user_input.lower() == 'clear':
                agent.clear_history()
                print("\n✓ Conversation history cleared.\n")
                continue

            # Skip empty input
            if not user_input:
                continue

            # Send message to AI and get response
            response = agent.send_message(user_input)

            # Display the response
            display_response(response)

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Thanks for chatting.")
            break
        except Exception as e:
            print(f"\n❌ An error occurred: {str(e)}\n")


if __name__ == "__main__":
    main()
