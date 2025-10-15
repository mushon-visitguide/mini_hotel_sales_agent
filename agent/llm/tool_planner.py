"""LLM-based tool planner using OpenAI Structured Outputs"""
import yaml
from pathlib import Path
from typing import Dict, Any
from .client import LLMClient
from .schemas import PlanningResult


class ToolPlanner:
    """
    LLM-based tool planner that outputs execution DAG.

    This replaces both intent detection and action planning with a single
    LLM call that:
    1. Understands what user wants (action description)
    2. Extracts parameters (slots)
    3. Plans which tools to call (tools DAG)

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

    def plan(self, user_message: str, debug: bool = False) -> PlanningResult:
        """
        Plan tool execution from user message using LLM.

        This uses OpenAI Structured Outputs to guarantee 100% schema adherence.
        The LLM outputs:
        - action: What user wants to do
        - slots: Extracted parameters
        - tools: DAG of tool calls with dependencies
        - reasoning: Why these tools were chosen

        Args:
            user_message: User's input message
            debug: If True, print debug information

        Returns:
            PlanningResult with action, slots, tools DAG, and reasoning

        Raises:
            RuntimeError: If LLM API call fails
        """
        # Build complete system prompt
        system_prompt = self._build_system_prompt()

        if debug:
            print(f"\n[ToolPlanner] Planning for: '{user_message}'")
            print(f"[ToolPlanner] Using model: {self.llm.model}")

        # Call LLM with Structured Outputs
        try:
            result = self.llm.structured_completion(
                system_prompt=system_prompt,
                user_message=user_message,
                response_schema=PlanningResult,
                temperature=0.0  # Deterministic for planning
            )

            if debug:
                print(f"[ToolPlanner] Action: {result.action}")
                print(f"[ToolPlanner] Slots: {result.slots.dict(exclude_none=True)}")
                print(f"[ToolPlanner] Tools ({len(result.tools)}):")
                for tool in result.tools:
                    deps = f"needs={tool.needs}" if tool.needs else "parallel"
                    print(f"  - {tool.id}: {tool.tool} ({deps})")
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

        # Add planner instructions
        planner_instructions = self.planner_prompt.get("system_prompt", "")

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
