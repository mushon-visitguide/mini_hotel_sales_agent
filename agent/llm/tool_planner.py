"""LLM-based tool planner using OpenAI Structured Outputs"""
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from .client import LLMClient
from .schemas import PlanningResult


class ToolPlanner:
    """
    LLM-based tool planner for agentic loop.

    Plans ONE WAVE at a time based on:
    1. User message
    2. Conversation history
    3. Previous tool results

    Uses OpenAI Structured Outputs for 100% reliable JSON schema adherence.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        prompts_dir: Path | str
    ):
        """
        Initialize tool planner.

        Args:
            llm_client: Configured LLM client
            prompts_dir: Path to prompts directory
        """
        self.llm = llm_client
        self.prompts_dir = Path(prompts_dir)

        # Load prompt configurations
        self.planner_prompt = self._load_prompt("planner.yaml")
        self.system_config = self._load_prompt("system/system.yaml")

    def _load_prompt(self, filename: str) -> Dict[str, Any]:
        """Load prompt configuration from YAML file"""
        prompt_file = self.prompts_dir / filename
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

        with open(prompt_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    async def plan(
        self,
        message: str,
        conversation_history: Optional[List[dict]] = None,
        previous_results: Optional[dict] = None,
        context: Optional[str] = None,
        debug: bool = False
    ) -> PlanningResult:
        """
        Plan NEXT wave of tools based on conversation history and previous results.

        AGENTIC LOOP MODE:
        - First call: Plan first wave based on user message
        - Subsequent calls: Plan next wave based on previous tool results
        - Returns status="done" when no more tools needed

        Args:
            message: Original user message
            conversation_history: List of conversation turns
            previous_results: Dict mapping tool_id to result from previous waves
            context: Optional conversation context (summary + recent messages)
            debug: Enable debug logging

        Returns:
            PlanningResult with status, action, slots, tools, and reasoning

        Raises:
            RuntimeError: If LLM API call fails
        """
        if conversation_history is None:
            conversation_history = [{"role": "user", "content": message}]

        # Prepend conversation context if provided
        if context:
            context_prefix = f"## Conversation Context\n{context}\n\n## Current User Message\n"
            conversation_history[-1]["content"] = context_prefix + conversation_history[-1]["content"]

        # Add previous results to context if available
        if previous_results:
            results_summary = "\n\n## Previous Tool Results:\n"
            for tool_id, result in previous_results.items():
                # Convert result to string for LLM consumption
                if isinstance(result, dict) and "error" not in result:
                    # Try JSON serialization with fallback for non-serializable objects
                    try:
                        result_str = json.dumps(result, indent=2, default=str)
                    except (TypeError, ValueError):
                        result_str = str(result)
                    results_summary += f"\n### {tool_id}:\n{result_str}\n"
                elif isinstance(result, str):
                    results_summary += f"\n### {tool_id}:\n{result}\n"
                else:
                    # Fallback to str() for any other type
                    results_summary += f"\n### {tool_id}:\n{str(result)}\n"

            # Add to last message
            conversation_history[-1]["content"] += results_summary

        # Build system prompt
        system_prompt = self._build_system_prompt()

        if debug:
            print(f"\n[ToolPlanner] Planning next wave")
            print(f"[ToolPlanner] Previous results: {list(previous_results.keys()) if previous_results else 'None'}")

        # LLM call
        try:
            result = self.llm.structured_completion(
                system_prompt=system_prompt,
                user_message=conversation_history[-1]["content"],
                response_schema=PlanningResult,
                temperature=0.0
            )

            if debug:
                print(f"[ToolPlanner] Action: {result.action}")
                print(f"[ToolPlanner] Tools ({len(result.tools)}): {[t.id for t in result.tools]}")
                print(f"[ToolPlanner] Reasoning: {result.reasoning}")

            return result

        except Exception as e:
            raise RuntimeError(f"Tool planning failed: {e}")

    def _build_system_prompt(self) -> str:
        """
        Build complete system prompt from configurations.

        Combines base system prompt + planner instructions + examples.
        """
        # Start with base system configuration
        base_prompt = self.system_config.get("prompt", "")

        # Add planner instructions with current date injected
        planner_instructions = self.planner_prompt.get("system_prompt", "")

        # Get current date in YYYY-MM-DD format (Asia/Jerusalem timezone)
        from zoneinfo import ZoneInfo
        current_date = datetime.now(ZoneInfo("Asia/Jerusalem")).strftime("%Y-%m-%d")
        planner_instructions = planner_instructions.replace("{current_date}", current_date)

        # Add examples for few-shot learning
        examples = self._format_examples()

        # Combine all parts
        full_prompt = f"{base_prompt}\n\n{planner_instructions}\n\n{examples}"

        return full_prompt

    def _format_examples(self) -> str:
        """Format examples from prompt config for few-shot learning"""
        examples = self.planner_prompt.get("examples", [])

        if not examples:
            return ""

        examples_text = "## EXAMPLES\n\n"

        for i, example in enumerate(examples, 1):
            user_msg = example.get("user", "")
            output = example.get("output", {})

            examples_text += f"**Example {i}:**\n"
            examples_text += f"User: \"{user_msg}\"\n"
            examples_text += f"Output:\n```json\n{yaml.dump(output, default_flow_style=False)}```\n\n"

        return examples_text


class ToolPlannerFactory:
    """Factory for creating ToolPlanner instances"""

    @staticmethod
    def create(
        api_key: str | None = None,
        prompts_dir: Path | str = "./prompts",
        model: str = "gpt-4o-2024-08-06"
    ) -> ToolPlanner:
        """
        Create ToolPlanner with default configuration.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            prompts_dir: Path to prompts directory
            model: OpenAI model to use

        Returns:
            Configured ToolPlanner instance
        """
        llm_client = LLMClient(api_key=api_key, model=model)
        return ToolPlanner(llm_client=llm_client, prompts_dir=prompts_dir)
