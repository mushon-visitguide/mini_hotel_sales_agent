"""Runtime executor for tool DAG with parallel execution"""
import asyncio
from typing import List, Dict, Any
from agent.llm.schemas import ToolCall
from agent.tools.registry import registry


class Runtime:
    """
    Executes tool DAG with parallel execution where possible.

    Key features:
    - Organizes tools into waves based on dependencies (needs)
    - Executes independent tools in parallel (wave-based)
    - Respects dependencies automatically
    - Timeout handling
    - Error recovery
    """

    def __init__(self, default_timeout: float = 30.0):
        """
        Initialize runtime executor.

        Args:
            default_timeout: Default timeout for tool calls in seconds
        """
        self.default_timeout = default_timeout

    async def execute(
        self,
        tools: List[ToolCall],
        credentials: Dict[str, Any],
        debug: bool = False
    ) -> Dict[str, Any]:
        """
        Execute tools DAG with parallel execution where possible.

        Algorithm:
        1. Organize tools into waves based on dependencies
        2. Execute each wave in parallel (all tools in wave run simultaneously)
        3. Pass results forward to dependent tools
        4. Return all results

        Args:
            tools: List of ToolCall from LLM planner
            credentials: PMS credentials to inject into tool args
            debug: Enable debug output

        Returns:
            Dict mapping tool IDs to their results

        Raises:
            ValueError: If circular dependencies detected
            TimeoutError: If any tool exceeds timeout
        """
        if not tools:
            return {}

        if debug:
            print(f"\n[Runtime] Executing {len(tools)} tools")

        # Track results
        results: Dict[str, Any] = {}

        # Organize into waves
        waves = self._organize_into_waves(tools)

        if debug:
            print(f"[Runtime] Organized into {len(waves)} waves")
            for i, wave in enumerate(waves):
                tool_names = [t.tool for t in wave]
                print(f"  Wave {i+1}: {tool_names}")

        # Execute each wave
        for wave_num, wave_tools in enumerate(waves):
            if debug:
                print(f"\n[Runtime] Executing wave {wave_num + 1}/{len(waves)} ({len(wave_tools)} tools in parallel)")

            # Execute all tools in this wave in parallel
            wave_results = await self._execute_wave(
                wave_tools,
                results,
                credentials,
                debug
            )

            # Merge results
            results.update(wave_results)

        if debug:
            print(f"\n[Runtime] Completed all {len(tools)} tools")

        return results

    def _organize_into_waves(self, tools: List[ToolCall]) -> List[List[ToolCall]]:
        """
        Organize tools into waves based on dependencies.

        Wave 0: Tools with no dependencies (needs=[])
        Wave 1: Tools that depend only on Wave 0
        Wave 2: Tools that depend on Wave 0 or 1
        etc.

        Example:
            Tools: A, B, C(needs=[A]), D(needs=[B, C])
            Waves: [[A, B], [C], [D]]

        Args:
            tools: List of ToolCall objects

        Returns:
            List of waves, where each wave is a list of tools that can run in parallel

        Raises:
            ValueError: If circular dependencies detected
        """
        waves: List[List[ToolCall]] = []
        remaining = list(tools)
        completed_ids = set()

        while remaining:
            # Find tools that can execute now (all dependencies met)
            ready = [
                tool for tool in remaining
                if all(dep_id in completed_ids for dep_id in tool.needs)
            ]

            if not ready:
                # Circular dependency or invalid plan
                remaining_ids = [t.id for t in remaining]
                raise ValueError(
                    f"Cannot resolve dependencies. "
                    f"Remaining tools: {remaining_ids}"
                )

            waves.append(ready)
            completed_ids.update(tool.id for tool in ready)
            remaining = [t for t in remaining if t not in ready]

        return waves

    async def _execute_wave(
        self,
        tools: List[ToolCall],
        previous_results: Dict[str, Any],
        credentials: Dict[str, Any],
        debug: bool
    ) -> Dict[str, Any]:
        """
        Execute all tools in a wave in parallel.

        Args:
            tools: Tools to execute
            previous_results: Results from previous waves
            credentials: PMS credentials
            debug: Enable debug output

        Returns:
            Dict mapping tool IDs to results
        """
        # Create tasks for each tool
        tasks = [
            self._execute_tool(tool, previous_results, credentials, debug)
            for tool in tools
        ]

        # Execute all in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Package results
        wave_results = {}
        for tool, result in zip(tools, results):
            if isinstance(result, Exception):
                error_msg = str(result)
                if debug:
                    print(f"  [Tool] {tool.id} FAILED: {error_msg}")
                wave_results[tool.id] = {"error": error_msg}
            else:
                if debug:
                    print(f"  [Tool] {tool.id} completed")
                wave_results[tool.id] = result

        return wave_results

    async def _execute_tool(
        self,
        tool: ToolCall,
        previous_results: Dict[str, Any],
        credentials: Dict[str, Any],
        debug: bool
    ) -> Any:
        """
        Execute a single tool with timeout.

        Args:
            tool: ToolCall to execute
            previous_results: Results from previous tools (for substitution)
            credentials: PMS credentials to inject
            debug: Enable debug output

        Returns:
            Tool result

        Raises:
            TimeoutError: If tool exceeds timeout
            Exception: If tool execution fails
        """
        # Merge tool args with credentials
        args = {**(tool.args or {}), **credentials}

        # Substitute args from previous results if needed
        args = self._substitute_args(args, previous_results)

        if debug:
            # Print args (redact credentials)
            safe_args = {
                k: "***REDACTED***" if k in ["pms_username", "pms_password"] else v
                for k, v in args.items()
            }
            print(f"  [Tool] {tool.id}: {tool.tool}({list(safe_args.keys())})")

        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                registry.call(tool.tool, **args),
                timeout=self.default_timeout
            )

            return result

        except asyncio.TimeoutError:
            raise TimeoutError(f"Tool {tool.tool} timed out after {self.default_timeout}s")

        except Exception as e:
            raise RuntimeError(f"Tool {tool.tool} failed: {e}")

    def _substitute_args(
        self,
        args: Dict[str, Any],
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Substitute arguments from previous step results.

        If an arg value is None, try to find it in previous results.

        Example:
            args = {"check_in": None, "check_out": None}
            previous_results = {"resolve_dates": {"check_in": "2024-10-19", ...}}

            Returns: {"check_in": "2024-10-19", "check_out": "2024-10-21"}

        Args:
            args: Tool arguments
            previous_results: Results from previous tools

        Returns:
            Arguments with substitutions
        """
        substituted = {}

        for key, value in args.items():
            if value is None:
                # Try to find this value in previous results
                found = self._find_in_results(key, previous_results)
                substituted[key] = found if found is not None else value
            else:
                substituted[key] = value

        return substituted

    def _find_in_results(
        self,
        key: str,
        results: Dict[str, Any]
    ) -> Any:
        """
        Find a key in nested results.

        Searches through all tool results for a matching key.

        Args:
            key: Key to find
            results: Tool results dict

        Returns:
            Value if found, None otherwise
        """
        for tool_result in results.values():
            if isinstance(tool_result, dict) and key in tool_result:
                return tool_result[key]
        return None
