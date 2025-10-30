"""Orchestrator with LLM-based tool planning and DAG execution"""
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from agent.llm import ToolPlanner, LLMClient
from agent.core.runtime import Runtime
from agent.tools.registry import registry
from agent.core.cancellation import CancellationToken, CancelledException
from agent.core.events import runtime_events
from agent.core.progress_notifier import ProgressNotifier
from agent.core.validator import ResultValidator

# Import conversation state management
from src.conversation import ContextManager

# Import tools to register them
from agent.tools.pms import tools as pms_tools  # noqa: F401
from agent.tools.faq import tools as faq_tools  # noqa: F401
from agent.tools.calendar import tools as calendar_tools  # noqa: F401
from agent.tools.availability import tools as availability_tools  # noqa: F401
from agent.tools.guest import tools as guest_tools  # noqa: F401

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Orchestrator with LLM-based tool planning and DAG execution.

    Flow:
    1. ToolPlanner outputs action + slots + tools DAG from user message
    2. Runtime executes tools DAG with parallel execution where possible
    3. Validation checks if results are sufficient
    4. Adaptation re-plans if needed (max 1 turn)
    5. Results returned
    """

    # Feedback loop safeguards
    MAX_ADAPTATION_TURNS = 1  # Allow 1 adaptation (2 total attempts: initial + 1 adaptation)
    MAX_TOTAL_TOOLS = 10  # Prevent tool spam

    def __init__(
        self,
        tool_planner: ToolPlanner,
        runtime: Runtime,
        prerun_calendar_tool: bool = False,
        progress_notifier: Optional[ProgressNotifier] = None,
        enable_feedback_loop: bool = True
    ):
        """
        Initialize orchestrator with LLM components.

        Args:
            tool_planner: LLM-based tool planner
            runtime: Tool execution runtime
            prerun_calendar_tool: If True, run calendar.resolve_date_hint in parallel with planner
                                  to save time when planner decides to use it
            progress_notifier: Optional progress notifier for WhatsApp/external messaging
            enable_feedback_loop: Enable adaptive feedback loop with validation
        """
        self.tool_planner = tool_planner
        self.runtime = runtime
        self.prerun_calendar_tool = prerun_calendar_tool
        self.progress_notifier = progress_notifier
        self.enable_feedback_loop = enable_feedback_loop
        self.validator = ResultValidator() if enable_feedback_loop else None

        logger.info("Orchestrator initialized with LLM-based tool planning")
        logger.info(f"Registered tools: {registry.list_tools()}")
        if prerun_calendar_tool:
            logger.info("Pre-run calendar tool: ENABLED (will run in parallel with planner)")
        if progress_notifier:
            logger.info("Progress notifications: ENABLED")
        if enable_feedback_loop:
            logger.info("Feedback loop: ENABLED (adaptive execution with validation)")

    @classmethod
    def create_default(
        cls,
        openai_api_key: Optional[str] = None,
        prompts_dir: Path | str = "./prompts",
        model: Optional[str] = None,
        runtime_timeout: float = 30.0,
        prerun_calendar_tool: bool = False
    ) -> "Orchestrator":
        """
        Factory method to create orchestrator with default configuration.

        Args:
            openai_api_key: OpenAI API key (defaults to env var)
            prompts_dir: Directory containing prompt files
            model: Model to use (defaults to LLM_MODEL env var or provider default)
            runtime_timeout: Default timeout for tool execution in seconds
            prerun_calendar_tool: If True, run calendar.resolve_date_hint in parallel with planner

        Returns:
            Configured Orchestrator instance
        """
        # Create LLM client (model=None will use env var or provider default)
        llm_client = LLMClient(api_key=openai_api_key, model=model)

        # Create tool planner
        tool_planner = ToolPlanner(
            llm_client=llm_client,
            prompts_dir=prompts_dir
        )

        # Create runtime
        runtime = Runtime(default_timeout=runtime_timeout)

        return cls(tool_planner, runtime, prerun_calendar_tool=prerun_calendar_tool)

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
        context_manager: Optional[ContextManager] = None,
        debug: bool = False,
        cancel_token: Optional[CancellationToken] = None
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
            context_manager: Optional context manager for stateful conversations
            debug: Enable debug output
            cancel_token: Optional cancellation token for graceful cancellation

        Returns:
            Results dictionary with action, slots, tools, and results

        Raises:
            CancelledException: If operation is cancelled via cancel_token
        """
        if debug:
            print("\n" + "=" * 70)
            print("[Orchestrator] Processing message")
            print("=" * 70)
            print(f"Message: {message}")
            print()

        # Start progress notification timing (resets message counter for new request)
        if self.progress_notifier:
            self.progress_notifier.start_request()
            if debug:
                print("[Orchestrator] Progress notifications started")

        # Add user message to conversation state if context manager provided
        if context_manager:
            await context_manager.add_user_message(message)
            if debug:
                print(f"[Orchestrator] Added to conversation state: {context_manager}")
                print()

        # OPTIMIZATION: Pre-run calendar tool in parallel with planner if flag enabled
        import asyncio
        prerun_calendar_task = None
        if self.prerun_calendar_tool:
            if debug:
                print("[Orchestrator] Pre-running calendar.resolve_date_hint in parallel with planner...")
            # Start calendar tool (will run in parallel with planner)
            prerun_calendar_task = asyncio.create_task(
                registry.call("calendar.resolve_date_hint", date_hint=message)
            )

        # Step 1: Plan tool execution using LLM
        try:
            # Build context for planner if we have conversation state
            context_prompt = None
            if context_manager:
                context_prompt = context_manager.build_context_for_planner()
                if debug and context_prompt:
                    print("[Orchestrator] Using conversation context:")
                    print(context_prompt)
                    print()

            planning_result = await self.tool_planner.plan(
                message,
                context=context_prompt,
                debug=debug
            )
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
            "pms_agency_channel_id": pms_agency_channel_id,
            "phone_number": context_manager.state.metadata.phone_number if context_manager else None
        }

        # Check if planner wants to use calendar tool and we pre-ran it
        prerun_results = {}
        if prerun_calendar_task:
            # Check if any planned tool is calendar.resolve_date_hint
            calendar_tool_ids = [
                tool.id for tool in planning_result.tools
                if tool.tool == "calendar.resolve_date_hint"
            ]

            if calendar_tool_ids:
                # Planner wants calendar results - wait for pre-run to complete
                try:
                    prerun_result = await prerun_calendar_task
                    # Cache result for all calendar tool IDs in the plan
                    for tool_id in calendar_tool_ids:
                        prerun_results[tool_id] = prerun_result
                    if debug:
                        print(f"[Orchestrator] ✓ Pre-run calendar result ready (saved {len(prerun_result) / 1024:.1f}KB)")
                        print(f"[Orchestrator] Cached for tool IDs: {calendar_tool_ids}")
                except Exception as e:
                    if debug:
                        print(f"[Orchestrator] Pre-run calendar failed: {e}, will run normally")
            else:
                # Planner doesn't need calendar tool - cancel pre-run task
                prerun_calendar_task.cancel()
                if debug:
                    print("[Orchestrator] Planner doesn't need calendar tool, pre-run cancelled")

        # Step 2: Execute tools DAG via runtime
        try:
            results = await self.runtime.execute(
                tools=planning_result.tools,
                credentials=pms_credentials,
                prerun_results=prerun_results,  # Pass pre-executed results
                debug=debug,
                cancel_token=cancel_token  # Pass cancellation token
            )
        except CancelledException as e:
            # Handle cancellation gracefully
            logger.info(f"Operation cancelled: {e.message}")
            if debug:
                print(f"\n[Orchestrator] Operation cancelled: {e.message}")
                print(f"[Orchestrator] Partial results available: {len(e.partial_results)}")

            # 🪝 Emit cancellation handled event
            await runtime_events.emit(
                'cancellation_handled',
                message=e.message,
                wave_num=e.wave_num,
                partial_results_count=len(e.partial_results)
            )

            # Return partial results with cancellation info
            return {
                "response": "Operation cancelled. Please send your message again.",
                "action": "operation_cancelled",
                "reasoning": e.message,
                "slots": planning_result.slots.dict(exclude_none=True),
                "tools": [t.id for t in planning_result.tools],
                "results": e.partial_results,
                "cancelled": True,
                "cancel_reason": e.message,
                "wave_cancelled_at": e.wave_num,
                "booking_status": context_manager.get_booking_status() if context_manager else None
            }
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            raise RuntimeError(f"Failed to execute tools: {e}")

        if debug:
            print("\n" + "=" * 70)
            print("[Orchestrator] Initial execution complete")
            print("=" * 70 + "\n")

        # Step 3: Validation & Adaptation Loop (if enabled)
        attempted_tools = set()
        all_results = dict(results)  # Start with initial results
        total_tools_executed = len(planning_result.tools)
        adaptation_turns = 0

        # Track attempted tool signatures
        for tool in planning_result.tools:
            sig = self._get_tool_signature(tool)
            attempted_tools.add(sig)

        if self.enable_feedback_loop and self.validator:
            for turn in range(self.MAX_ADAPTATION_TURNS):
                # Check cancellation before validation
                if cancel_token and cancel_token.is_cancelled:
                    raise CancelledException(
                        "Cancelled during validation",
                        wave_num=turn + 1,
                        partial_results=all_results
                    )

                # Validate results
                validation = await self.validator.analyze_results(
                    user_message=message,
                    plan_action=planning_result.action,
                    tools=planning_result.tools,
                    results=all_results
                )

                # 🪝 Emit validation event
                await runtime_events.emit(
                    'validation_complete',
                    needs_adaptation=validation.needs_adaptation,
                    issues_count=len(validation.issues),
                    turn=turn
                )

                if debug:
                    print(f"\n[Orchestrator] Validation turn {turn}: "
                          f"needs_adaptation={validation.needs_adaptation}, "
                          f"issues={len(validation.issues)}")

                # Check if adaptation needed
                if not validation.needs_adaptation:
                    logger.info("Results are valid, no adaptation needed")
                    break

                # Check if we've hit limits
                if total_tools_executed >= self.MAX_TOTAL_TOOLS:
                    logger.warning(f"Hit max tools limit ({self.MAX_TOTAL_TOOLS}), stopping adaptation")
                    break

                # Check cancellation before adaptation
                if cancel_token and cancel_token.is_cancelled:
                    raise CancelledException(
                        "Cancelled before adaptation",
                        wave_num=turn + 1,
                        partial_results=all_results
                    )

                # 🪝 Emit adaptation started event
                await runtime_events.emit(
                    'adaptation_started',
                    turn=turn,
                    reason=validation.feedback
                )

                if debug:
                    print(f"\n[Orchestrator] Adapting plan...")
                    print(f"[Orchestrator] Validation feedback: {validation.feedback}")

                # Notify user of adaptation (if progress notifier available)
                if self.progress_notifier:
                    try:
                        self.progress_notifier.send_message("🔄 Trying alternatives...")
                    except Exception as e:
                        logger.warning(f"Failed to send adaptation progress: {e}")

                # Get adapted plan from planner
                adapted_plan = await self.tool_planner.adapt(
                    original_message=message,
                    original_plan=planning_result,
                    original_results=all_results,
                    validation_feedback=validation.feedback or "Results insufficient",
                    attempted_tools=attempted_tools,
                    debug=debug
                )

                # Check if planner gave up (no new tools)
                if not adapted_plan.tools:
                    logger.info("Planner returned no new tools, stopping adaptation")
                    if debug:
                        print("[Orchestrator] No alternative tools suggested, using current results")
                    break

                # Filter out duplicates and apply limits
                new_tools = []
                for tool in adapted_plan.tools:
                    sig = self._get_tool_signature(tool)

                    if sig in attempted_tools:
                        logger.warning(f"Skipping duplicate tool: {tool.tool}")
                        if debug:
                            print(f"[Orchestrator] Skipping duplicate: {tool.tool}")
                        continue

                    if total_tools_executed + len(new_tools) + 1 > self.MAX_TOTAL_TOOLS:
                        logger.warning("Would exceed max tools, stopping")
                        break

                    attempted_tools.add(sig)
                    new_tools.append(tool)

                if not new_tools:
                    logger.info("No valid new tools after filtering duplicates")
                    break

                # Check cancellation before executing adapted tools
                if cancel_token and cancel_token.is_cancelled:
                    raise CancelledException(
                        "Cancelled during adaptation",
                        wave_num=turn + 1,
                        partial_results=all_results
                    )

                # Execute adapted tools
                logger.info(f"Adaptation turn {turn + 1}: executing {len(new_tools)} new tools")
                if debug:
                    print(f"\n[Orchestrator] Executing {len(new_tools)} adapted tools...")
                    for tool in new_tools:
                        print(f"  - {tool.tool}")

                try:
                    additional_results = await self.runtime.execute(
                        tools=new_tools,
                        credentials=pms_credentials,
                        debug=debug,
                        cancel_token=cancel_token
                    )

                    # Merge new results
                    all_results.update(additional_results)
                    total_tools_executed += len(new_tools)
                    adaptation_turns = turn + 1

                    # 🪝 Emit adaptation complete event
                    await runtime_events.emit(
                        'adaptation_complete',
                        turn=turn + 1,
                        tools_executed=len(new_tools),
                        success=True
                    )

                    if debug:
                        print(f"[Orchestrator] Adaptation turn {turn + 1} complete")

                except CancelledException as e:
                    # Cancellation during adaptation - merge partial results and re-raise
                    all_results.update(e.partial_results)
                    raise CancelledException(
                        f"Cancelled during adaptation: {e.message}",
                        wave_num=e.wave_num,
                        partial_results=all_results
                    )
                except Exception as e:
                    logger.error(f"Adaptation execution failed: {e}")
                    # Don't fail completely - use results we have
                    break

        # Use all_results (includes adapted results) for the rest of the flow
        results = all_results

        if debug:
            print("\n" + "=" * 70)
            print("[Orchestrator] All execution complete")
            print(f"[Orchestrator] Total tools executed: {total_tools_executed}")
            print(f"[Orchestrator] Adaptation turns: {adaptation_turns}")
            print("=" * 70 + "\n")

        # Update conversation state if context manager provided
        if context_manager:
            # Update booking context from extracted slots
            slots_dict = planning_result.slots.dict(exclude_none=True)

            # Extract important data from tool results and save to context
            for tool_call in planning_result.tools:
                tool_result = results.get(tool_call.id)

                # Calendar tools → extract dates
                if tool_call.tool.startswith("calendar.") and isinstance(tool_result, dict):
                    if "check_in" in tool_result and tool_result["check_in"]:
                        slots_dict["check_in"] = tool_result["check_in"]
                    if "check_out" in tool_result and tool_result["check_out"]:
                        slots_dict["check_out"] = tool_result["check_out"]

                # Guest info tool → extract contact info (if not already in slots)
                if tool_call.tool == "guest.get_guest_info" and isinstance(tool_result, str):
                    # Tool result is formatted string, but we already have the info in slots
                    # No additional extraction needed - guest info comes from slots
                    pass

            context_manager.update_booking_context(slots_dict)

            # Add tool executions to conversation history
            tool_executions = []
            for tool_call in planning_result.tools:
                tool_id = tool_call.id
                tool_result = results.get(tool_id)

                # Determine success
                is_error = isinstance(tool_result, dict) and 'error' in tool_result
                success = not is_error
                error_message = tool_result.get('error') if is_error else None

                tool_executions.append({
                    "tool_name": tool_call.tool,
                    "tool_id": tool_id,
                    "inputs": tool_call.args,
                    "result": tool_result,
                    "success": success,
                    "error_message": error_message
                })

            # Batch add tool executions (will compress outputs)
            await context_manager.add_tool_executions_batch(tool_executions)

            if debug:
                print(f"[Orchestrator] Updated conversation state")
                print(f"[Orchestrator] Booking status: {context_manager.get_booking_status()}")
                print()

        # Generate natural language response
        response = None
        if context_manager:
            from agent.llm.responder import ResponseGenerator

            try:
                responder = ResponseGenerator()

                # Get current tool executions (the ones we just added)
                current_tool_results = context_manager.get_recent_tool_executions(len(planning_result.tools))

                response = await responder.generate_response(
                    user_message=message,
                    recent_messages=context_manager.get_recent_messages(5),
                    current_tool_results=current_tool_results,
                    planner_action=planning_result.action,
                    missing_required_parameters=planning_result.missing_required_parameters,
                    host_guidance_prompt=context_manager.state.metadata.host_guidance_prompt,
                    debug=debug
                )

                # Save assistant response to conversation
                await context_manager.add_assistant_message(response)

                if debug:
                    print(f"[Orchestrator] Generated response:")
                    print(f"{response}")
                    print()

            except Exception as e:
                logger.error(f"Response generation failed: {e}")
                # Fallback to action if response generation fails
                response = planning_result.action
        else:
            # No context manager - use action as response
            response = planning_result.action

        # Return results with response
        return {
            "response": response,                    # Natural language response for user
            "action": planning_result.action,
            "reasoning": planning_result.reasoning,
            "slots": planning_result.slots.dict(exclude_none=True),
            "tools": [t.id for t in planning_result.tools],
            "results": results,                      # Keep for debugging
            "booking_status": context_manager.get_booking_status() if context_manager else None,
            "total_tools_executed": total_tools_executed if 'total_tools_executed' in locals() else len(planning_result.tools),
            "adaptation_turns": adaptation_turns if 'adaptation_turns' in locals() else 0
        }

    def _get_tool_signature(self, tool) -> str:
        """
        Create signature to detect duplicate tool calls.

        Uses tool name + key arguments to identify unique calls.
        This prevents the adaptation loop from trying the exact same
        tool call that already failed.

        Args:
            tool: ToolCall object

        Returns:
            String signature like "pms.get_availability:hash(args)"
        """
        # Extract key arguments that define uniqueness
        key_args = {}
        if tool.args:
            for key in ['check_in', 'check_out', 'adults', 'children', 'date_hint', 'guest_id']:
                if key in tool.args:
                    key_args[key] = tool.args[key]

        # Create stable hash of key arguments
        try:
            args_hash = hash(frozenset(key_args.items()))
        except TypeError:
            # If args contain unhashable types, use string repr
            args_hash = hash(str(sorted(key_args.items())))

        return f"{tool.tool}:{args_hash}"
