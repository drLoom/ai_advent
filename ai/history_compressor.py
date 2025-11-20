import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)


class HistoryCompressor:
    """
    Manages conversation history compression by summarizing old messages
    to reduce token usage while maintaining conversation context.
    """

    def __init__(
        self,
        client,
        compression_threshold: int = 10,
        keep_recent: int = 4,
        model: str = "google/gemini-2.5-flash-lite-preview-09-2025"
    ):
        """
        Initialize the history compressor.

        Args:
            client: OpenRouterClient instance for API calls
            compression_threshold: Number of messages before triggering compression
            keep_recent: Number of recent messages to keep uncompressed
            model: Model to use for summarization (use a fast, cheap model)
        """
        self.client = client
        self.compression_threshold = compression_threshold
        self.keep_recent = keep_recent
        self.model = model
        self.compression_stats = {
            "total_compressions": 0,
            "tokens_before": 0,
            "tokens_after": 0,
            "messages_compressed": 0
        }

    def should_compress(self, conversation_history: List[Dict]) -> bool:
        """
        Check if conversation history should be compressed.

        Args:
            conversation_history: List of message dictionaries

        Returns:
            bool: True if compression should be triggered
        """
        # Filter out system messages for counting
        user_assistant_messages = [
            msg for msg in conversation_history
            if msg.get("role") in ["user", "assistant"]
        ]

        return len(user_assistant_messages) >= self.compression_threshold

    def compress_history(
        self, conversation_history: List[Dict]
    ) -> Tuple[List[Dict], Dict]:
        """
        Compress conversation history by summarizing old messages.

        Args:
            conversation_history: List of message dictionaries

        Returns:
            Tuple of (compressed_history, compression_metrics)
        """
        if not conversation_history:
            return conversation_history, {}

        # Separate system messages, old messages, and recent messages
        system_messages = [
            msg for msg in conversation_history
            if msg.get("role") == "system"
        ]

        user_assistant_messages = [
            msg for msg in conversation_history
            if msg.get("role") in ["user", "assistant"]
        ]

        if len(user_assistant_messages) < self.compression_threshold:
            logger.info("Not enough messages to compress")
            return conversation_history, {}

        # Split into messages to compress and messages to keep
        messages_to_compress = user_assistant_messages[:-self.keep_recent]
        recent_messages = user_assistant_messages[-self.keep_recent:]

        logger.info(
            f"Compressing {len(messages_to_compress)} messages, "
            f"keeping {len(recent_messages)} recent messages"
        )

        # Estimate tokens before compression (rough estimate: ~4 chars per token)
        tokens_before = self._estimate_tokens(messages_to_compress)

        # Generate summary of old messages
        summary = self._generate_summary(messages_to_compress)

        # Estimate tokens after compression
        tokens_after = self._estimate_tokens([{"role": "system", "content": summary}])

        # Create compressed history
        compressed_history = system_messages + [
            {
                "role": "system",
                "content": f"Previous conversation summary:\n{summary}"
            }
        ] + recent_messages

        # Update stats
        self.compression_stats["total_compressions"] += 1
        self.compression_stats["tokens_before"] += tokens_before
        self.compression_stats["tokens_after"] += tokens_after
        self.compression_stats["messages_compressed"] += len(messages_to_compress)

        compression_metrics = {
            "messages_compressed": len(messages_to_compress),
            "messages_kept": len(recent_messages),
            "estimated_tokens_before": tokens_before,
            "estimated_tokens_after": tokens_after,
            "estimated_tokens_saved": tokens_before - tokens_after,
            "compression_ratio": round(tokens_after / tokens_before * 100, 2) if tokens_before > 0 else 0
        }

        logger.info(f"Compression metrics: {compression_metrics}")

        return compressed_history, compression_metrics

    def _generate_summary(self, messages: List[Dict]) -> str:
        """
        Generate a concise summary of messages using AI.

        Args:
            messages: List of message dictionaries to summarize

        Returns:
            str: Summary text
        """
        # Format messages for summarization
        conversation_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in messages
        ])

        summary_prompt = f"""Summarize the following conversation concisely, preserving key information, decisions, and context that would be needed to continue the conversation naturally.

Be brief but comprehensive. Focus on:
- Main topics discussed
- Important facts or information shared
- Any decisions or conclusions reached
- User preferences or requirements mentioned

Conversation:
{conversation_text}

Summary:"""

        try:
            response_data = self.client.send_chat_completion(
                messages=[{"role": "user", "content": summary_prompt}],
                model=self.model,
                temperature=0.3  # Low temperature for consistent summaries
            )

            summary = response_data["choices"][0]["message"]["content"]
            logger.info(f"Generated summary: {summary[:100]}...")

            return summary

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            # Fallback: create a simple text summary
            return f"Previous conversation covered {len(messages)} messages about various topics."

    def _estimate_tokens(self, messages: List[Dict]) -> int:
        """
        Estimate token count for messages.
        Uses rough heuristic of ~4 characters per token.

        Args:
            messages: List of message dictionaries

        Returns:
            int: Estimated token count
        """
        total_chars = sum(len(msg.get("content", "")) for msg in messages)
        return total_chars // 4

    def get_stats(self) -> Dict:
        """
        Get compression statistics.

        Returns:
            dict: Compression statistics
        """
        stats = self.compression_stats.copy()
        if stats["tokens_before"] > 0:
            stats["total_tokens_saved"] = stats["tokens_before"] - stats["tokens_after"]
            stats["overall_compression_ratio"] = round(
                stats["tokens_after"] / stats["tokens_before"] * 100, 2
            )
        return stats
