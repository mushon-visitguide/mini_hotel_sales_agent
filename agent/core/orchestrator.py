"""Orchestrator with LLM-based tool planning and DAG execution"""
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from agent.llm import ToolPlanner, LLMClient
from agent.core.runtime import Runtime
from agent.tools.registry import registry

# Import tools to register them
from agent.tools.pms import tools as pms_tools  # noqa: F401
from agent.tools.faq import tools as faq_tools  # noqa: F401
from agent.tools.calendar import tools as calendar_tools  # noqa: F401

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Orchestrator with LLM-based tool planning and DAG execution.

    Flow:
    1. ToolPlanner outputs action + slots + tools DAG from user message
    2. Runtime executes tools DAG with parallel execution where possible
    3. Results returned
    """

    def __init__(
        self,
        tool_planner: ToolPlanner,
        runtime: Runtime
    ):
        """
        Initialize orchestrator with LLM components.

        Args:
            tool_planner: LLM-based tool planner
            runtime: Tool execution runtime
        """
        self.tool_planner = tool_planner
        self.runtime = runtime

        logger.info("Orchestrator initialized with LLM-based tool planning")
        logger.info(f"Registered tools: {registry.list_tools()}")

    @classmethod
    def create_default(
        cls,
        openai_api_key: Optional[str] = None,
        prompts_dir: Path | str = "./prompts",
        model: str = "gpt-4.1",
        runtime_timeout: float = 30.0
    ) -> "Orchestrator":
        """
        Factory method to create orchestrator with default configuration.

        Args:
            openai_api_key: OpenAI API key (defaults to env var)
            prompts_dir: Directory containing prompt files
            model: OpenAI model to use
            runtime_timeout: Default timeout for tool execution in seconds

        Returns:
            Configured Orchestrator instance
        """
        # Create LLM client
        llm_client = LLMClient(api_key=openai_api_key, model=model)

        # Create tool planner
        tool_planner = ToolPlanner(
            llm_client=llm_client,
            prompts_dir=prompts_dir
        )

        # Create runtime
        runtime = Runtime(default_timeout=runtime_timeout)

        return cls(tool_planner, runtime)

    async def process_message(
        self,
        message: str,
        pms_type: str,
        pms_username: str,
        pms_password: str,
        hotel_id: str,
        pms_use_sandbox: bool = False,
        pms_url_code: Optional[str] = None,
        pms_agency_channel_id: Optional[int] = None,
        debug: bool = False
    ) -> Dict[str, Any]:
        """
        Process message with LLM-based tool planning.

        Args:
            message: User message
            pms_type: PMS system type
            pms_username: PMS username
            pms_password: PMS password
            hotel_id: Hotel identifier
            pms_use_sandbox: Use sandbox mode
            pms_url_code: URL code for MiniHotel
            pms_agency_channel_id: Agency channel for EzGo
            debug: Enable debug output

        Returns:
            Results dictionary with action, slots, tools, and results
        """
        if debug:
            print("\n" + "=" * 70)
            print("[Orchestrator] Processing message")
            print("=" * 70)
            print(f"Message: {message}")
            print()

        # Step 1: Plan tool execution using LLM
        try:
            planning_result = await self.tool_planner.plan(message, debug=debug)
        except Exception as e:
            logger.error(f"Tool planning failed: {e}")
            raise RuntimeError(f"Failed to plan tool execution: {e}")

        if debug:
            print(f"\n[Orchestrator] Action: {planning_result.action}")
            print(f"[Orchestrator] Reasoning: {planning_result.reasoning}")
            print(f"[Orchestrator] Extracted slots:")
            for key, value in planning_result.slots.dict(exclude_none=True).items():
                print(f"  - {key}: {value}")
            print(f"[Orchestrator] Planned tools ({len(planning_result.tools)}):")
            for tool in planning_result.tools:
                deps = f"needs={tool.needs}" if tool.needs else "parallel"
                print(f"  - {tool.id}: {tool.tool} ({deps})")

        # Build credentials dict
        pms_credentials = {
            "pms_type": pms_type,
            "pms_username": pms_username,
            "pms_password": pms_password,
            "hotel_id": hotel_id,
            "pms_use_sandbox": pms_use_sandbox,
            "pms_url_code": pms_url_code,
            "pms_agency_channel_id": pms_agency_channel_id
        }

        # Step 2: Execute tools DAG via runtime
        try:
            results = await self.runtime.execute(
                tools=planning_result.tools,
                credentials=pms_credentials,
                debug=debug
            )
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            raise RuntimeError(f"Failed to execute tools: {e}")

        if debug:
            print("\n" + "=" * 70)
            print("[Orchestrator] Execution complete")
            print("=" * 70 + "\n")

        # Return results
        return {
            "action": planning_result.action,
            "reasoning": planning_result.reasoning,
            "slots": planning_result.slots.dict(exclude_none=True),
            "tools": [t.id for t in planning_result.tools],
            "results": results
        }
