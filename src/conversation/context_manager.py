"""
Context window manager for conversations.

Provides high-level interface for managing conversation state with:
- Automatic summarization when context grows too large
- Sliding window of recent messages
- Tool execution history with compressed outputs
- Booking context tracking
"""
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from agent.llm import LLMClient
from src.conversation.state import ConversationState
from src.conversation.summarizer import summarize_conversation, should_trigger_summarization
from src.conversation.compressor import compress_tool_output

logger = logging.getLogger(__name__)


class ContextManager:
    """
    High-level context window manager.

    This class provides the main interface for managing conversation state
    with automatic context optimization (summarization, compression).
    """

    def __init__(
        self,
        state: ConversationState,
        llm_client: Optional[LLMClient] = None,
        summarize_every_n_turns: int = 5,
        keep_recent_messages: int = 5,
        keep_recent_tools: int = 3
    ):
        """
        Initialize context manager.

        Args:
            state: Conversation state to manage
            llm_client: LLM client for summarization (creates default if not provided)
            summarize_every_n_turns: Trigger summarization every N turns
            keep_recent_messages: Number of recent messages in sliding window
            keep_recent_tools: Number of recent tool executions to keep
        """
        self.state = state
        self.llm_client = llm_client
        self.summarize_every_n_turns = summarize_every_n_turns
        self.keep_recent_messages = keep_recent_messages
        self.keep_recent_tools = keep_recent_tools

    @classmethod
    def create(
        cls,
        session_id: str,
        hotel_id: Optional[str] = None,
        pms_type: Optional[str] = None,
        phone_number: Optional[str] = None,
        host_guidance_prompt: Optional[str] = None,
        storage_dir: Optional[Path] = None,
        llm_client: Optional[LLMClient] = None,
        **kwargs
    ) -> "ContextManager":
        """
        Factory method to create or load context manager.

        Args:
            session_id: Session identifier
            hotel_id: Hotel ID
            pms_type: PMS type
            phone_number: Guest phone number for session authentication
            host_guidance_prompt: Hotel-specific guidance for response generation
            storage_dir: Storage directory for sessions
            llm_client: LLM client for summarization
            **kwargs: Additional arguments for ContextManager

        Returns:
            ContextManager instance
        """
        state = ConversationState.create_or_load(
            session_id=session_id,
            hotel_id=hotel_id,
            pms_type=pms_type,
            phone_number=phone_number,
            host_guidance_prompt=host_guidance_prompt,
            storage_dir=storage_dir
        )

        return cls(state=state, llm_client=llm_client, **kwargs)

    # === Message Management ===

    async def add_user_message(self, message: str) -> None:
        """
        Add user message and trigger summarization if needed.

        Args:
            message: User message content
        """
        self.state.add_user_message(message)

        # Check if we should summarize
        await self._check_and_summarize()

        # Save state
        self.state.save()

    async def add_assistant_message(self, message: str) -> None:
        """
        Add assistant message.

        Args:
            message: Assistant message content
        """
        self.state.add_assistant_message(message)
        self.state.save()

    # === Tool Execution Management ===

    async def add_tool_execution(
        self,
        tool_name: str,
        tool_id: str,
        inputs: Dict[str, Any],
        full_result: Any,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> None:
        """
        Add tool execution with automatic output compression.

        Args:
            tool_name: Name of the tool executed
            tool_id: Unique ID for this execution
            inputs: Input parameters
            full_result: Full tool result (will be compressed)
            success: Whether tool executed successfully
            error_message: Error message if failed
        """
        # Compress tool output
        if success and full_result:
            output_summary, output_metadata = compress_tool_output(tool_name, full_result)
        else:
            output_summary = error_message or "Tool execution failed"
            output_metadata = {"error": True}

        # Add to state
        self.state.add_tool_execution(
            tool_name=tool_name,
            tool_id=tool_id,
            inputs=inputs,
            output_summary=output_summary,
            output_metadata=output_metadata,
            success=success,
            error_message=error_message
        )

        logger.debug(f"Added tool execution: {tool_id} (compressed: {len(output_summary)} chars)")

        self.state.save()

    async def add_tool_executions_batch(
        self,
        executions: List[Dict[str, Any]]
    ) -> None:
        """
        Add multiple tool executions at once.

        Args:
            executions: List of execution dicts with keys:
                - tool_name
                - tool_id
                - inputs
                - result
                - success (optional)
                - error_message (optional)
        """
        for execution in executions:
            await self.add_tool_execution(
                tool_name=execution["tool_name"],
                tool_id=execution["tool_id"],
                inputs=execution["inputs"],
                full_result=execution["result"],
                success=execution.get("success", True),
                error_message=execution.get("error_message")
            )

    # === Booking Context ===

    def update_booking_context(self, slots: Dict[str, Any]) -> None:
        """
        Update booking context from extracted slots.

        Args:
            slots: Extracted slots from planner
        """
        self.state.update_booking_context(slots)
        self.state.save()

    def get_booking_status(self) -> Dict[str, Any]:
        """
        Get current booking status.

        Returns:
            Dict with ready status and missing info
        """
        return {
            "ready_for_booking": self.state.is_ready_for_booking(),
            "missing_info": self.state.get_missing_booking_info(),
            "booking_context": self.state.booking_context.to_dict()
        }

    # === Context Building ===

    def build_context_for_planner(self) -> str:
        """
        Build optimized context prompt for tool planner.

        Returns context with:
        1. Conversation summary (if exists)
        2. Current booking context
        3. Recent tool executions (last N)
        4. Recent messages (sliding window)

        Returns:
            Context prompt string
        """
        return self.state.build_context_prompt(
            include_recent_messages=self.keep_recent_messages,
            include_recent_tools=self.keep_recent_tools
        )

    def get_recent_messages(self, limit: int) -> List:
        """
        Get recent messages for response generation.

        Args:
            limit: Maximum number of recent messages to return

        Returns:
            List of recent Message objects
        """
        return self.state.get_recent_messages(limit)

    def get_recent_tool_executions(self, limit: int) -> List:
        """
        Get recent tool executions for response generation.

        Args:
            limit: Maximum number of recent tool executions to return

        Returns:
            List of recent ToolExecutionSummary objects
        """
        return self.state.get_recent_tool_executions(limit)

    def get_context_stats(self) -> Dict[str, Any]:
        """
        Get statistics about current context state.

        Useful for debugging and monitoring context usage.

        Returns:
            Dict with context statistics
        """
        context_prompt = self.build_context_for_planner()

        return {
            "session_id": self.state.metadata.session_id,
            "total_turns": self.state.metadata.total_turns,
            "total_messages": self.state.metadata.total_messages,
            "total_tool_executions": self.state.metadata.total_tool_executions,
            "has_summary": self.state.conversation_summary is not None,
            "last_summarized_turn": self.state.metadata.last_summarized_turn,
            "context_prompt_length": len(context_prompt),
            "recent_messages_count": len(self.state.get_recent_messages(self.keep_recent_messages)),
            "recent_tools_count": len(self.state.get_recent_tool_executions(self.keep_recent_tools))
        }

    # === Summarization ===

    async def _check_and_summarize(self) -> None:
        """
        Check if summarization is needed and trigger it (accumulative).

        Called automatically after adding messages.
        """
        if not self.state.should_summarize(self.summarize_every_n_turns):
            return

        logger.info(
            f"Triggering summarization for session {self.state.metadata.session_id} "
            f"(turn {self.state.metadata.total_turns})"
        )

        try:
            # Get NEW messages since last summary (accumulative approach)
            last_summarized = self.state.metadata.last_summarized_turn
            new_messages = [
                msg for msg in self.state.messages
                if msg.turn_number > last_summarized
            ]

            # Get NEW tool executions since last summary
            new_tools = [
                tool for tool in self.state.tool_executions
                if tool.turn_number > last_summarized
            ]

            # Generate accumulative summary (includes previous summary + new messages)
            summary = summarize_conversation(
                messages=new_messages,
                tool_executions=new_tools,
                llm_client=self.llm_client,
                previous_summary=self.state.conversation_summary  # Pass previous summary
            )

            # Update state
            self.state.set_summary(summary)

            logger.info(
                f"Summarization complete: {len(summary)} chars, "
                f"version {self.state.metadata.summary_version}, "
                f"summarized {len(new_messages)} new messages"
            )

        except Exception as e:
            logger.error(f"Summarization failed: {e}", exc_info=True)
            # Don't fail the whole operation if summarization fails

    async def force_summarize(self) -> str:
        """
        Force summarization regardless of turn count.

        Returns:
            Generated summary text
        """
        summary = summarize_conversation(
            messages=self.state.messages,
            tool_executions=self.state.tool_executions,
            llm_client=self.llm_client
        )

        self.state.set_summary(summary)
        self.state.save()

        return summary

    # === Persistence ===

    def save(self) -> None:
        """Save conversation state to disk"""
        self.state.save()

    def clear(self) -> None:
        """
        Clear all conversation state (reset to new session).

        Useful for testing or starting fresh conversation.
        """
        # Keep session ID but reset everything else
        session_id = self.state.metadata.session_id
        hotel_id = self.state.metadata.hotel_id
        pms_type = self.state.metadata.pms_type
        storage_dir = self.state.storage_dir

        # Create fresh state
        self.state = ConversationState(
            session_id=session_id,
            hotel_id=hotel_id,
            pms_type=pms_type,
            storage_dir=storage_dir
        )
        self.state.save()

        logger.info(f"Cleared conversation state for session {session_id}")

    # === Debugging ===

    def get_full_state(self) -> Dict[str, Any]:
        """
        Get complete state dump for debugging.

        Returns:
            Full state dictionary
        """
        return {
            "booking_context": self.state.booking_context.to_dict(),
            "messages": [msg.to_dict() for msg in self.state.messages],
            "tool_executions": [tool.to_dict() for tool in self.state.tool_executions],
            "metadata": self.state.metadata.to_dict(),
            "conversation_summary": self.state.conversation_summary
        }

    def __str__(self) -> str:
        """Human-readable representation"""
        return (
            f"ContextManager(session={self.state.metadata.session_id}, "
            f"turns={self.state.metadata.total_turns}, "
            f"messages={len(self.state.messages)}, "
            f"tools={len(self.state.tool_executions)})"
        )
