#!/usr/bin/env python3
"""
Simple CLI tool to send messages to OpenRouter API.
Usage: python main.py --message "Your message here"
"""

import argparse
import sys
from ai.client import OpenRouterClient


def main():
    """Parse CLI arguments and send message to OpenRouter."""
    parser = argparse.ArgumentParser(
        description="Send a message to OpenRouter API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--message", "-m", type=str, required=True, help="Message to send to the AI"
    )

    parser.add_argument(
        "--temperature",
        "-t",
        type=float,
        default=0.7,
        help="Temperature for response generation (default: 0.7)",
    )

    parser.add_argument(
        "--model",
        type=str,
        default="kwaipilot/kat-coder-pro:free",
        help="Model to use (default: kwaipilot/kat-coder-pro:free)",
    )

    args = parser.parse_args()

    try:
        client = OpenRouterClient()
        messages = [{"role": "user", "content": args.message}]
        print(f"📤 Sending message to {args.model}...")

        response_data = client.send_chat_completion(
            messages=messages, model=args.model, temperature=args.temperature
        )

        format_response(response_data)

    except ValueError as e:
        print(f"❌ Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


def format_response(response_data):
    ai_message = response_data["choices"][0]["message"]["content"]
    print("\n" + "=" * 50)
    print("🤖 AI Response:")
    print("=" * 50)
    print(ai_message)
    print("=" * 50 + "\n")

    usage = response_data.get("usage", {})
    if usage:
        print(f"📊 Usage: {usage.get('total_tokens', 'N/A')} tokens")


if __name__ == "__main__":
    main()
