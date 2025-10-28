"""
Conversation summarization using LLM.

Generates concise summaries of conversation history to reduce context size
while preserving key information about user intent, decisions, and state.
"""
from typing import List, Optional
from agent.llm import LLMClient
from src.models.conversation import Message, ToolExecutionSummary


SUMMARIZATION_SYSTEM_PROMPT = """Please summarize the conversation, focusing specifically on what the user requested.

When summarizing, prioritize:
1. What the user asked for (their requests, questions, needs)
2. Key details the user provided (dates, number of guests, preferences, constraints)
3. What information was retrieved for the user
4. Any decisions or selections the user made
5. What the user still needs or what remains unresolved

Keep the summary concise (3-5 sentences) and focused on the user's perspective and their requests.

Example:
"User requested availability for tomorrow, 2 adults. Showed 13 available rooms (480-810 ILS). User asked about room 228A capacity and features. Explained 228A accommodates up to 8 guests with 2 bedrooms, jacuzzi, kitchen (810 ILS/night). User still needs to provide name and contact info to complete booking."
"""


def summarize_conversation(
    messages: List[Message],
    tool_executions: Optional[List[ToolExecutionSummary]] = None,
    llm_client: Optional[LLMClient] = None,
    previous_summary: Optional[str] = None,
    model: str = "gpt-4.1",
    max_tokens: int = 300
) -> str:
    """
    Generate LLM-based summary of conversation (accumulative).

    Args:
        messages: List of NEW messages to summarize (since last summary)
        tool_executions: Optional list of tool executions to include
        llm_client: LLM client to use (creates default if not provided)
        previous_summary: Previous summary to build upon (for accumulative summarization)
        model: Model to use for summarization
        max_tokens: Maximum tokens for summary (default: 300 for ~200-250 words)

    Returns:
        Concise summary text (includes previous summary + new conversation)
    """
    if not messages:
        return previous_summary or "No conversation yet."

    # Create LLM client if not provided
    if llm_client is None:
        llm_client = LLMClient(model=model)

    # Build conversation text to summarize
    conversation_text = _format_conversation_for_summary(messages, tool_executions)

    # Call LLM for summarization
    try:
        if previous_summary:
            # Accumulative: Include previous summary and new messages
            prompt = f"""Previous summary:
{previous_summary}

New conversation since then:
{conversation_text}

Please provide an updated summary that combines the previous summary with the new conversation."""
        else:
            # First time: Just summarize from scratch
            prompt = f"Summarize this conversation:\n\n{conversation_text}"

        messages_for_llm = [
            {"role": "system", "content": SUMMARIZATION_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
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
