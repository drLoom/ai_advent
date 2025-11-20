# History Compression Feature

## Overview

The History Compression feature automatically summarizes old conversation messages to reduce token usage while maintaining conversation context. This helps manage costs and stay within token limits during long conversations.

## How It Works

### Compression Trigger
- Compression is triggered when the conversation reaches a threshold (default: 10 messages)
- The system keeps the most recent messages (default: 4) uncompressed
- Older messages are summarized into a concise context summary

### Compression Process
1. **Detection**: After each message, the system checks if compression is needed
2. **Separation**: Messages are split into "old" (to compress) and "recent" (to keep)
3. **Summarization**: Old messages are sent to a fast, cheap AI model for summarization
4. **Replacement**: The summary replaces the old messages in the history
5. **Continuation**: The conversation continues with the compressed history

### Example
```
Before compression (10 messages):
- System: You are a helpful assistant
- User: What is Python?
- AI: Python is a programming language...
- User: What are its features?
- AI: Python has many features...
- User: Tell me about lists
- AI: Lists are mutable...
- User: What about tuples?
- AI: Tuples are immutable...
- User: How do I use decorators?  ← Message #10, compression triggers

After compression (5 messages):
- System: You are a helpful assistant
- System: Previous conversation summary: User asked about Python basics, features, data structures like lists and tuples...
- User: What about tuples?
- AI: Tuples are immutable...
- User: How do I use decorators?
```

## Configuration

### Backend Configuration (conversation.py)
```python
conversation = Conversation(
    model='your-model',
    enable_compression=True,        # Enable/disable compression
    compression_threshold=10,       # Trigger after N messages
    keep_recent=4                   # Keep last N messages uncompressed
)
```

### UI Controls (chat.html)
- **Checkbox**: "History Compression" toggle in the UI
- **Visual Feedback**: Orange notification when compression occurs
- **Metrics Display**: Shows tokens saved and compression ratio

## Metrics

The system tracks and displays:
- **Messages Compressed**: Number of old messages summarized
- **Messages Kept**: Number of recent messages preserved
- **Estimated Tokens Before**: Token count before compression
- **Estimated Tokens After**: Token count after compression
- **Estimated Tokens Saved**: Reduction in tokens
- **Compression Ratio**: Percentage of original size (lower is better)

### Example Metrics Display
```
🗜️ History Compressed:
Compressed 6 messages into a summary,
keeping 4 recent messages.
Saved ~850 tokens (25% of original size).
```

## Testing

### Manual Testing
1. Start the server: `python server.py`
2. Open the chat interface
3. Send 10+ messages to trigger compression
4. Observe the orange compression notification
5. Verify the AI maintains conversation context

### Automated Testing
Run the test script to compare with/without compression:
```bash
python test_compression.py
```

This will:
1. Run a 12-message conversation WITH compression
2. Run the same conversation WITHOUT compression
3. Compare token usage and savings
4. Display detailed metrics

### Expected Results
- **Token Savings**: 20-40% reduction in total tokens
- **Context Quality**: AI should maintain coherent conversation
- **Response Quality**: Minimal degradation after compression

## Implementation Details

### Files Modified/Created

1. **ai/history_compressor.py** (NEW)
   - `HistoryCompressor` class
   - Compression logic and summarization
   - Token estimation and metrics tracking

2. **conversation.py** (MODIFIED)
   - Integrated `HistoryCompressor`
   - Added compression parameters to `__init__`
   - Added compression trigger in `process_message`
   - Added compression metrics to response

3. **server.py** (MODIFIED)
   - Accept `enable_compression` parameter from frontend
   - Pass it to `Conversation` class

4. **static/js/chat.js** (MODIFIED)
   - `addCompressionMessage()` function for UI display
   - Send `enable_compression` to backend
   - Display compression notifications

5. **static/css/style.css** (MODIFIED)
   - Styling for compression message (orange theme)

6. **templates/chat.html** (MODIFIED)
   - Added compression checkbox control

7. **test_compression.py** (NEW)
   - Automated test suite
   - Comparison analysis

## Best Practices

### When to Enable Compression
- ✅ Long conversations (>10 messages)
- ✅ Production environments with token limits
- ✅ Cost-sensitive applications
- ✅ General chatbot use cases

### When to Disable Compression
- ❌ Very short conversations (<10 messages)
- ❌ When every detail must be preserved exactly
- ❌ Debugging or testing specific conversation flows
- ❌ When context quality is more important than cost

### Tuning Parameters

**compression_threshold**
- Lower (5-8): More aggressive compression, more savings, potential context loss
- Default (10): Balanced approach
- Higher (15-20): Conservative compression, better context, less savings

**keep_recent**
- Lower (2-3): More compression, risk of losing recent context
- Default (4): Maintains immediate context well
- Higher (6-8): Less compression benefit, very safe

## Token Estimation

The system uses a rough heuristic: **~4 characters per token**

This works well for:
- English text
- Code snippets
- Mixed content

Actual token counts may vary based on:
- Model tokenizer
- Language (non-English may differ)
- Special characters and formatting

## Model Selection for Summarization

The compressor uses a fast, cheap model for summarization:
- Default: `google/gemini-2.5-flash-lite-preview-09-2025`
- Temperature: 0.3 (for consistent summaries)
- Goal: Balance quality and cost

### Alternative Models
- **More quality**: Use a stronger model (higher cost)
- **More speed**: Use a faster model (potential quality loss)
- **More savings**: Use a cheaper model (test quality first)

## Monitoring

### Logs
Watch for these log messages:
```
🗜️ Triggering history compression...
✅ Compression complete. Metrics: {...}
```

### Metrics to Track
1. **Compression Events**: How often compression occurs
2. **Token Savings**: Average savings per compression
3. **Compression Ratio**: Efficiency of summarization
4. **Conversation Quality**: User satisfaction after compression

## Future Enhancements

Potential improvements:
1. **Adaptive Thresholds**: Adjust based on message length
2. **Semantic Compression**: Keep important messages, compress filler
3. **Multi-level Compression**: Re-compress old summaries
4. **Custom Summarization**: Domain-specific summary prompts
5. **Token Counting**: Use actual tokenizer instead of estimation
6. **Compression History**: Track and display all compression events

## Troubleshooting

### Compression Not Triggering
- Check `enable_compression` is `True`
- Verify conversation has enough messages (>= threshold)
- Check logs for errors in summarization

### Poor Context Quality
- Increase `keep_recent` parameter
- Increase `compression_threshold`
- Review summarization prompt in `history_compressor.py`
- Consider using a better summarization model

### High API Costs
- Compression itself requires API calls
- For very short conversations, disable compression
- Use a cheaper model for summarization

### UI Not Showing Compression
- Check browser console for errors
- Verify compression metrics in response JSON
- Ensure CSS is loaded correctly
- Clear browser cache

## API Reference

### HistoryCompressor Class

```python
class HistoryCompressor:
    def __init__(
        self,
        client,                    # OpenRouterClient instance
        compression_threshold=10,  # Trigger threshold
        keep_recent=4,            # Recent messages to keep
        model="..."               # Summarization model
    )

    def should_compress(self, conversation_history: List[Dict]) -> bool:
        """Check if compression should trigger"""

    def compress_history(
        self, conversation_history: List[Dict]
    ) -> Tuple[List[Dict], Dict]:
        """Compress history and return metrics"""

    def get_stats(self) -> Dict:
        """Get cumulative compression statistics"""
```

### Response Format

```json
{
  "success": true,
  "message": "AI response...",
  "model": "nvidia/nemotron-nano-12b-v2-vl",
  "usage": {
    "prompt_tokens": 120,
    "completion_tokens": 50,
    "total_tokens": 170
  },
  "compression": {
    "messages_compressed": 6,
    "messages_kept": 4,
    "estimated_tokens_before": 850,
    "estimated_tokens_after": 210,
    "estimated_tokens_saved": 640,
    "compression_ratio": 24.7
  },
  "conversation_history": [...]
}
```

## License

This feature is part of the main project and follows the same license.
