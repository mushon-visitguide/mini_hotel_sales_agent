"""Response Generator - Creates natural user-facing responses from tool outputs"""
from typing import List, Optional, Dict
from agent.llm.client import LLMClient
from src.models.conversation import Message, ToolExecutionSummary


class ResponseGenerator:
    """
    Generates natural language responses for users based on tool outputs.

    Key principle: Uses ONLY tool results from current turn, not internal state.
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize response generator.

        Args:
            llm_client: LLM client (creates default if not provided)
        """
        self.llm = llm_client or LLMClient()

    async def generate_response(
        self,
        user_message: str,
        recent_messages: List[Message],
        current_tool_results: List[ToolExecutionSummary],
        planner_action: str,
        missing_required_parameters: Optional[Dict[str, str]] = None,
        host_guidance_prompt: Optional[str] = None
    ) -> str:
        """
        Generate natural response based ONLY on tool outputs from current turn.

        Args:
            user_message: The user's current message
            recent_messages: Recent conversation messages (for context)
            current_tool_results: Tool executions from THIS turn only (compressed)
            planner_action: What the planner said it's doing
            missing_required_parameters: Map of missing required params to descriptions
            host_guidance_prompt: Hotel-specific guidance (HIGHEST PRIORITY)

        Returns:
            Natural language response for the user
        """
        # Build the prompt
        prompt = self._build_prompt(
            user_message=user_message,
            recent_messages=recent_messages,
            current_tool_results=current_tool_results,
            missing_required_parameters=missing_required_parameters,
            host_guidance_prompt=host_guidance_prompt
        )

        # Get response from LLM
        system_prompt = self._get_system_prompt(host_guidance_prompt=host_guidance_prompt)
        messages = [
            {"role": "user", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        # Print the entire prompt in blue
        print("\033[94m" + "=" * 70)
        print("[RESPONSE GENERATOR PROMPT]")
        print("=" * 70)
        print("\n### SYSTEM PROMPT:")
        print(system_prompt)
        print("\n### USER PROMPT:")
        print(prompt)
        print("=" * 70 + "\033[0m")

        response = self.llm.chat_completion(
            messages=messages,
            temperature=0.7,  # Slightly creative for natural conversation
            max_tokens=500
        )

        return response.strip()

    def _get_system_prompt(self, host_guidance_prompt: Optional[str] = None) -> str:
        """Get the system prompt with optional host guidance at highest priority"""

        base_prompt = """You are a hotel guest service assistant.

CRITICAL: Answer using ONLY the information provided you here
- NEVER invent prices, room names, dates, or availability
- NEVER use your general hotel knowledge or make assumptions
- If you need information that wasn't retrieved → Ask for it

Be warm, conversational, and helpful. If information is missing, ask the guest for it politely.

Respond or ask with the shortest message that achieves first-contact resolution: classify (silently) the intent as Binary, Transactional, or Exploratory and size the reply accordingly.
For Binary, return a one-line verdict only—add one critical condition only if it changes the outcome.
For Transactional, proactively include the three decision essentials (current availability or next best, headline price/range, one defining spec like room type) plus one clear next step; ask at most one missing detail if it blocks completion.
For Exploratory, give a 3-bullet micro-summary then offer "More details?"; always mirror the user's tone, use digits/symbols, **one line**, brief **micro-empathy** when appropriate, and keep compliance invisible; when blocked, ask waht you need but **prefer no justification**.

Sometimes reflect the things you know the guest from the guest info so he will you as AI knows about his reservation
"""

        # Inject host guidance at the TOP with highest priority
        if host_guidance_prompt:
            return f"""🔴 HOST GUIDANCE (HIGHEST PRIORITY - FOLLOW THIS ABOVE ALL OTHER INSTRUCTIONS):
{host_guidance_prompt}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{base_prompt}"""

        return base_prompt

    def _build_prompt(
        self,
        user_message: str,
        recent_messages: List[Message],
        current_tool_results: List[ToolExecutionSummary],
        missing_required_parameters: Optional[Dict[str, str]] = None,
        host_guidance_prompt: Optional[str] = None
    ) -> str:
        """Build the ultra-minimal prompt with only essential info"""

        parts = []

        # Recent conversation (last 5 messages for context)
        # Exclude the current message (last one) to avoid duplication with "Guest's Question"
        if recent_messages and len(recent_messages) > 1:
            parts.append("## Recent Conversation")
            for msg in recent_messages[-5:-1]:  # All but the last message
                role_display = msg.role.value.upper()
                parts.append(f"{role_display}: {msg.content}")
            parts.append("")

        # Tool results from THIS turn (compressed summaries)
        if current_tool_results:
            parts.append("## Information Retrieved")
            for tool in current_tool_results:
                status = "✓" if tool.success else "✗"
                parts.append(f"[{status}] {tool.output_summary}")
            parts.append("")

        # Missing required parameters (when planner couldn't proceed)
        if missing_required_parameters:
            parts.append("## Missing Required Information")
            parts.append("These parameters are needed to proceed:")
            for param_name, param_description in missing_required_parameters.items():
                parts.append(f"  - {param_description}")
            parts.append("")
            parts.append("Ask the guest for this information conversationally.")
            parts.append("")

        # Current question
        parts.append("## Guest's Question")
        parts.append(f"{user_message}")
        parts.append("")
        parts.append("Respond naturally:")

        return "\n".join(parts)
