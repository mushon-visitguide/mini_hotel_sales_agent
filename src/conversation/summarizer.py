"""
Conversation summarization using LLM.

Generates concise summaries of conversation history to reduce context size
while preserving key information about user intent, decisions, and state.
"""
from typing import List, Optional
from agent.llm import LLMClient
from src.models.conversation import Message, ToolExecutionSummary


SUMMARIZATION_SYSTEM_PROMPT = """You are a conversation summarizer for a hotel booking assistant.

Your task is to create a concise summary of the conversation that captures:
1. User's intent and goals (what they're trying to book/learn)
2. Key information gathered (dates, guests, preferences)
3. Decisions made (room selections, price points discussed)
4. Questions asked and answered
5. Current state (what's been resolved, what's pending)

Focus on facts and information that matter for continuing the conversation.
Be very concise - aim for 3-5 sentences maximum.

Example good summary:
"User looking to book 2 rooms for family reunion, December 15-20 (5 nights), 2 adults + 2 children per room. Checked availability - found 13 rooms ranging 800-2500 ILS/night. User interested in 228A apartment (8 guests, 2BR, jacuzzi, 1850 ILS/night). Still need guest contact information to complete booking."

Example bad summary:
"The user said hello and then asked about availability. Then I showed them some rooms. They asked about prices. Then they selected a room."
"""


def summarize_conversation(
    messages: List[Message],
    tool_executions: Optional[List[ToolExecutionSummary]] = None,
    llm_client: Optional[LLMClient] = None,
    model: str = "gpt-4.1",
    max_tokens: int = 300
) -> str:
    """
    Generate LLM-based summary of conversation.

    Args:
        messages: List of messages to summarize
        tool_executions: Optional list of tool executions to include
        llm_client: LLM client to use (creates default if not provided)
        model: Model to use for summarization
        max_tokens: Maximum tokens for summary (default: 300 for ~200-250 words)

    Returns:
        Concise summary text
    """
    if not messages:
        return "No conversation yet."

    # Create LLM client if not provided
    if llm_client is None:
        llm_client = LLMClient(model=model)

    # Build conversation text to summarize
    conversation_text = _format_conversation_for_summary(messages, tool_executions)

    # Call LLM for summarization
    try:
        messages_for_llm = [
            {"role": "system", "content": SUMMARIZATION_SYSTEM_PROMPT},
            {"role": "user", "content": f"Summarize this conversation:\n\n{conversation_text}"}
        ]

        summary = llm_client.chat_completion(
            messages=messages_for_llm,
            temperature=0.3,  # Low temperature for consistent summaries
            max_tokens=max_tokens
        )

        return summary.strip()

    except Exception as e:
        # Fallback to simple summary if LLM fails
        return _create_fallback_summary(messages, tool_executions)


def _format_conversation_for_summary(
    messages: List[Message],
    tool_executions: Optional[List[ToolExecutionSummary]] = None
) -> str:
    """
    Format conversation into text for LLM summarization.

    Creates a readable transcript with tool executions interleaved.
    """
    lines = []

    # Group tool executions by turn if provided
    tools_by_turn = {}
    if tool_executions:
        for tool in tool_executions:
            turn = tool.turn_number
            if turn not in tools_by_turn:
                tools_by_turn[turn] = []
            tools_by_turn[turn].append(tool)

    # Format messages with tool executions
    current_turn = None
    for msg in messages:
        # Add tool executions for this turn (before the message)
        if msg.turn_number and msg.turn_number != current_turn:
            current_turn = msg.turn_number
            if current_turn in tools_by_turn:
                for tool in tools_by_turn[current_turn]:
                    status = "✓" if tool.success else "✗"
                    lines.append(f"[Tool {status}] {tool.tool_name}: {tool.output_summary}")

        # Add message
        lines.append(f"{msg.role.value.upper()}: {msg.content}")

    return "\n".join(lines)


def _create_fallback_summary(
    messages: List[Message],
    tool_executions: Optional[List[ToolExecutionSummary]] = None
) -> str:
    """
    Create simple fallback summary without LLM.

    Used if LLM summarization fails.
    """
    user_messages = [msg for msg in messages if msg.role.value == "user"]
    assistant_messages = [msg for msg in messages if msg.role.value == "assistant"]

    parts = [
        f"Conversation with {len(messages)} messages "
        f"({len(user_messages)} from user, {len(assistant_messages)} from assistant)."
    ]

    # Add tool execution summary
    if tool_executions:
        successful_tools = [t for t in tool_executions if t.success]
        parts.append(f"Executed {len(successful_tools)} tools successfully.")

        # Mention key tool types
        tool_types = set()
        for tool in tool_executions:
            if "availability" in tool.tool_name:
                tool_types.add("availability check")
            elif "faq" in tool.tool_name:
                tool_types.add("FAQ lookup")
            elif "calendar" in tool.tool_name:
                tool_types.add("date resolution")
            elif "booking" in tool.tool_name:
                tool_types.add("booking link")

        if tool_types:
            parts.append(f"Tools used: {', '.join(tool_types)}.")

    # Add first user message as intent
    if user_messages:
        first_msg = user_messages[0].content[:100]
        parts.append(f"Started with: '{first_msg}'")

    return " ".join(parts)


def should_trigger_summarization(
    total_turns: int,
    last_summarized_turn: int,
    summarize_every_n_turns: int = 5
) -> bool:
    """
    Determine if conversation should be summarized.

    Args:
        total_turns: Total conversation turns so far
        last_summarized_turn: Turn number when last summarized
        summarize_every_n_turns: Summarize every N turns

    Returns:
        True if summarization should be triggered
    """
    return (total_turns - last_summarized_turn) >= summarize_every_n_turns
