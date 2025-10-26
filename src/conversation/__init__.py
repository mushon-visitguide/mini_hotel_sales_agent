"""
Conversation state management package.

This package provides stateful conversation handling including:
- Conversation state tracking (booking context, tool history)
- Tool output compression for context efficiency
- LLM-based conversation summarization
- Context window management (sliding window + summary)

Main components:
- ConversationState: Manages complete conversation state
- compress_tool_output: Compresses large tool outputs to summaries
- summarize_conversation: Creates LLM-based summaries of older messages
- ContextManager: Manages context window with sliding window + summary
"""

from .state import ConversationState
from .compressor import compress_tool_output
from .summarizer import summarize_conversation
from .context_manager import ContextManager

__all__ = [
    "ConversationState",
    "compress_tool_output",
    "summarize_conversation",
    "ContextManager",
]
