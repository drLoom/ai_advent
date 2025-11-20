"""
Test script to compare conversation quality and token usage with and without compression.
"""
import logging
from conversation import Conversation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_test_conversation():
    """Create a test conversation with multiple exchanges."""
    conversation_history = []
    test_messages = [
        "Hello! What is Python?",
        "What are the key features of Python?",
        "Can you explain list comprehensions?",
        "What's the difference between lists and tuples?",
        "How do I handle exceptions in Python?",
        "What are decorators?",
        "Explain the concept of generators",
        "What is the difference between a module and a package?",
        "How do I use virtual environments?",
        "What are the best practices for Python projects?",
        "Tell me about Python's async/await syntax",
        "How do I optimize Python code for performance?"
    ]

    return test_messages


def test_with_compression():
    """Test conversation with compression enabled."""
    logger.info("\n" + "="*80)
    logger.info("Testing WITH COMPRESSION (threshold=10, keep_recent=4)")
    logger.info("="*80)

    conv = Conversation(
        model='nvidia/nemotron-nano-12b-v2-vl',
        temperature=0.7,
        enable_compression=True,
        compression_threshold=10,
        keep_recent=4
    )

    conversation_history = []
    test_messages = create_test_conversation()

    total_tokens_input = 0
    total_tokens_output = 0
    compression_events = []

    for i, message in enumerate(test_messages, 1):
        logger.info(f"\n--- Message {i}/{len(test_messages)} ---")
        logger.info(f"User: {message}")
        logger.info(f"History size before: {len(conversation_history)} messages")

        response = conv.process_message(
            user_message=message,
            conversation_history=conversation_history
        )

        if response.get("success"):
            logger.info(f"AI: {response['message'][:100]}...")

            # Track token usage
            usage = response.get("usage", {})
            total_tokens_input += usage.get("prompt_tokens", 0)
            total_tokens_output += usage.get("completion_tokens", 0)

            # Track compression events
            if response.get("compression"):
                compression_events.append({
                    "at_message": i,
                    "metrics": response["compression"]
                })
                logger.info(f"🗜️ COMPRESSION occurred: {response['compression']}")

            conversation_history = response["conversation_history"]
            logger.info(f"History size after: {len(conversation_history)} messages")

    logger.info("\n" + "="*80)
    logger.info("WITH COMPRESSION - SUMMARY")
    logger.info("="*80)
    logger.info(f"Total messages processed: {len(test_messages)}")
    logger.info(f"Total input tokens: {total_tokens_input}")
    logger.info(f"Total output tokens: {total_tokens_output}")
    logger.info(f"Total tokens: {total_tokens_input + total_tokens_output}")
    logger.info(f"Number of compression events: {len(compression_events)}")

    if compression_events:
        total_saved = sum(e["metrics"]["estimated_tokens_saved"] for e in compression_events)
        logger.info(f"Estimated tokens saved from compression: {total_saved}")

    # Get compressor stats
    if conv.compressor:
        stats = conv.compressor.get_stats()
        logger.info(f"\nCompressor statistics: {stats}")

    return {
        "total_tokens": total_tokens_input + total_tokens_output,
        "input_tokens": total_tokens_input,
        "output_tokens": total_tokens_output,
        "compression_events": len(compression_events),
        "final_history_size": len(conversation_history)
    }


def test_without_compression():
    """Test conversation without compression."""
    logger.info("\n" + "="*80)
    logger.info("Testing WITHOUT COMPRESSION")
    logger.info("="*80)

    conv = Conversation(
        model='nvidia/nemotron-nano-12b-v2-vl',
        temperature=0.7,
        enable_compression=False
    )

    conversation_history = []
    test_messages = create_test_conversation()

    total_tokens_input = 0
    total_tokens_output = 0

    for i, message in enumerate(test_messages, 1):
        logger.info(f"\n--- Message {i}/{len(test_messages)} ---")
        logger.info(f"User: {message}")
        logger.info(f"History size: {len(conversation_history)} messages")

        response = conv.process_message(
            user_message=message,
            conversation_history=conversation_history
        )

        if response.get("success"):
            logger.info(f"AI: {response['message'][:100]}...")

            # Track token usage
            usage = response.get("usage", {})
            total_tokens_input += usage.get("prompt_tokens", 0)
            total_tokens_output += usage.get("completion_tokens", 0)

            conversation_history = response["conversation_history"]

    logger.info("\n" + "="*80)
    logger.info("WITHOUT COMPRESSION - SUMMARY")
    logger.info("="*80)
    logger.info(f"Total messages processed: {len(test_messages)}")
    logger.info(f"Total input tokens: {total_tokens_input}")
    logger.info(f"Total output tokens: {total_tokens_output}")
    logger.info(f"Total tokens: {total_tokens_input + total_tokens_output}")
    logger.info(f"Final history size: {len(conversation_history)} messages")

    return {
        "total_tokens": total_tokens_input + total_tokens_output,
        "input_tokens": total_tokens_input,
        "output_tokens": total_tokens_output,
        "compression_events": 0,
        "final_history_size": len(conversation_history)
    }


def main():
    """Run both tests and compare results."""
    print("\n" + "🧪 COMPRESSION TEST SUITE" + "\n")
    print("This will test the conversation with and without history compression")
    print("to compare token usage and conversation quality.\n")

    # Test with compression
    results_with = test_with_compression()

    print("\n" + "⏸️  Press Enter to continue with test WITHOUT compression...")
    input()

    # Test without compression
    results_without = test_without_compression()

    # Compare results
    logger.info("\n" + "="*80)
    logger.info("COMPARISON")
    logger.info("="*80)

    token_savings = results_without["total_tokens"] - results_with["total_tokens"]
    token_savings_percent = (token_savings / results_without["total_tokens"] * 100) if results_without["total_tokens"] > 0 else 0

    logger.info(f"\n📊 Token Usage:")
    logger.info(f"  Without compression: {results_without['total_tokens']} tokens")
    logger.info(f"  With compression:    {results_with['total_tokens']} tokens")
    logger.info(f"  Savings:             {token_savings} tokens ({token_savings_percent:.1f}%)")

    logger.info(f"\n💬 History Size:")
    logger.info(f"  Without compression: {results_without['final_history_size']} messages")
    logger.info(f"  With compression:    {results_with['final_history_size']} messages")

    logger.info(f"\n🗜️ Compression Events: {results_with['compression_events']}")

    logger.info("\n" + "="*80)
    logger.info("✅ Test suite completed!")
    logger.info("="*80)
    logger.info("\nNote: To test conversation quality, review the logs above to see")
    logger.info("how well the AI maintained context after compression events.")


if __name__ == "__main__":
    main()
