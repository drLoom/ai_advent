#!/usr/bin/env python3
"""
Simple CLI tool to send messages to OpenRouter API.
Usage: python main.py --message "Your message here"
"""

import argparse

from cli.parse_review import parse_review


def main():
    parser = argparse.ArgumentParser(
        description="Send a message to OpenRouter API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    review_parser = subparsers.add_parser("parse_review", help="Parse review message")

    review_parser.add_argument("--review", type=str, help="Review text")
    review_parser.set_defaults(func=parse_review)

    args = parser.parse_args()
    args.func(args)


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
