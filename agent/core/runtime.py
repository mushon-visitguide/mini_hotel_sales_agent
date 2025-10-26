"""Runtime executor for tool DAG with parallel execution"""
import asyncio
from typing import List, Dict, Any
from agent.llm.schemas import ToolCall
from agent.tools.registry import registry
from agent.tools.availability.tools import summarize_multi_room_mixed, summarize_multi_room_simple


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

            # Auto-summarize multi-room availability if detected
            wave_results = await self._post_process_multi_room(
                wave_tools,
                wave_results,
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

        # Substitute args from previous results if needed, respecting dependencies
        args = self._substitute_args(args, previous_results, tool.needs)

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
        previous_results: Dict[str, Any],
        dependency_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Substitute arguments from previous step results.

        IMPORTANT: Only looks at results from tools specified in dependency_ids.
        This ensures that when multiple tools return the same keys (e.g., check_in),
        each dependent tool gets values from the correct source.

        Example:
            args = {"check_in": None, "check_out": None}
            previous_results = {
                "resolve_hanukkah": {"check_in": "2025-12-14", ...},
                "resolve_tomorrow": {"check_in": "2025-10-16", ...}
            }
            dependency_ids = ["resolve_tomorrow"]

            Returns: {"check_in": "2025-10-16", "check_out": "2025-10-17"}
                     (from resolve_tomorrow only, NOT from resolve_hanukkah)

        Args:
            args: Tool arguments
            previous_results: Results from ALL previous tools
            dependency_ids: List of tool IDs this tool depends on (from 'needs' field)

        Returns:
            Arguments with substitutions
        """
        substituted = {}

        for key, value in args.items():
            if value is None:
                # Only search in results from dependencies
                found = self._find_in_results(key, previous_results, dependency_ids)
                substituted[key] = found if found is not None else value
            else:
                substituted[key] = value

        return substituted

    def _find_in_results(
        self,
        key: str,
        results: Dict[str, Any],
        dependency_ids: List[str]
    ) -> Any:
        """
        Find a key in results from specific dependencies.

        ONLY searches through results from tools listed in dependency_ids.
        This prevents cross-contamination when multiple parallel tools return the same keys.

        Example:
            key = "check_in"
            results = {
                "resolve_hanukkah": {"check_in": "2025-12-14"},
                "resolve_tomorrow": {"check_in": "2025-10-16"},
                "other_tool": {"check_in": "2025-01-01"}
            }
            dependency_ids = ["resolve_tomorrow"]

            Returns: "2025-10-16" (ONLY from resolve_tomorrow, ignores others)

        Args:
            key: Key to find
            results: ALL tool results
            dependency_ids: List of tool IDs to search in (from 'needs' field)

        Returns:
            Value if found in dependencies, None otherwise
        """
        # Only search in specified dependencies
        for dep_id in dependency_ids:
            if dep_id in results:
                dep_result = results[dep_id]
                if isinstance(dep_result, dict) and key in dep_result:
                    return dep_result[key]
        return None

    async def _post_process_multi_room(
        self,
        wave_tools: List[ToolCall],
        wave_results: Dict[str, Any],
        debug: bool
    ) -> Dict[str, Any]:
        """
        Auto-detect and summarize multi-room availability requests.

        When multiple pms.get_availability_and_pricing calls are made in the same wave,
        automatically run the appropriate summarizer and inject results.

        Args:
            wave_tools: Tools that were executed in this wave
            wave_results: Results from the wave
            debug: Enable debug output

        Returns:
            Updated results with multi-room summary if applicable
        """
        # Find all pms.get_availability_and_pricing calls in this wave
        availability_calls = [
            (tool, wave_results.get(tool.id))
            for tool in wave_tools
            if tool.tool == "pms.get_availability_and_pricing" and wave_results.get(tool.id) and "error" not in wave_results.get(tool.id, {})
        ]

        # Need at least 2 availability calls for multi-room
        if len(availability_calls) < 2:
            return wave_results

        if debug:
            print(f"\n[Runtime] Detected {len(availability_calls)} availability calls - auto-summarizing multi-room booking")

        # Extract occupancies and results
        room_requirements = []
        availability_results = []

        for tool, result in availability_calls:
            args = tool.args or {}
            room_requirements.append({
                "adults": args.get("adults", 2),
                "children": args.get("children", 0),
                "babies": args.get("babies", 0)
            })
            availability_results.append(result)

        # Determine if all occupancies are the same
        first_occupancy = room_requirements[0]
        all_same = all(
            req["adults"] == first_occupancy["adults"] and
            req["children"] == first_occupancy["children"] and
            req["babies"] == first_occupancy["babies"]
            for req in room_requirements
        )

        try:
            if all_same:
                # Simple case - same occupancy for all rooms
                if debug:
                    print(f"[Runtime] Using simple summarizer (same occupancy: {first_occupancy['adults']}A, {first_occupancy['children']}C, {first_occupancy['babies']}B)")

                # Use first result as the availability data
                summary = await summarize_multi_room_simple(
                    availability_data=availability_results[0],
                    rooms_needed=len(availability_calls)
                )
            else:
                # Mixed case - different occupancies
                if debug:
                    print(f"[Runtime] Using mixed summarizer (different occupancies)")

                summary = await summarize_multi_room_mixed(
                    availability_results=availability_results,
                    room_requirements=room_requirements
                )

            # Inject summary into results with special key
            wave_results["_multi_room_summary"] = summary

            if debug:
                print(f"[Runtime] Multi-room summary: can_fulfill={summary.get('can_fulfill')}, options={len(summary.get('options', []))}")

        except Exception as e:
            if debug:
                print(f"[Runtime] Multi-room summarization failed: {e}")
            # Don't fail the whole request, just skip summarization

        return wave_results
