# Agentic Loop Refactoring - Implementation Steps

## ✅ Completed

### 1. Schema Updates (`agent/llm/schemas.py`)
- ✅ Added `status: Literal["continue", "done"]` field to `PlanningResult`
- ✅ Removed `needs` field from `ToolCall` (no more DAG dependencies)
- ✅ Updated docstrings to explain agentic loop
- ✅ Updated examples to show two-wave planning

## 🔄 In Progress - Next Steps

### 2. Update Orchestrator (`agent/core/orchestrator.py`)

Replace the current single-plan execution with agentic loop:

```python
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
) -> dict:
    """Process message with agentic loop"""

    # Build conversation history
    conversation_history = [{"role": "user", "content": message}]

    # Prepare credentials for tools
    credentials = {
        "pms_type": pms_type,
        "pms_username": pms_username,
        "pms_password": pms_password,
        "hotel_id": hotel_id,
        "pms_use_sandbox": pms_use_sandbox,
        "pms_url_code": pms_url_code,
        "pms_agency_channel_id": pms_agency_channel_id
    }

    all_results = {}
    iteration = 0
    max_iterations = 5
    final_planning_result = None

    if debug:
        print("\n" + "=" * 70)
        print("[Orchestrator] Processing message (Agentic Loop Mode)")
        print("=" * 70)
        print(f"Message: {message}\n")

    # AGENTIC LOOP: Plan → Execute → Re-plan → Execute → ... → Done
    while iteration < max_iterations:
        if debug:
            print(f"\n{'=' * 70}")
            print(f"[Orchestrator] Iteration {iteration + 1}/{max_iterations}")
            print(f"{'=' * 70}\n")

        # LLM plans NEXT wave
        planning_result = await self.tool_planner.plan(
            message=message,
            conversation_history=conversation_history,
            previous_results=all_results,
            debug=debug
        )

        final_planning_result = planning_result

        # Check if done
        if planning_result.status == "done":
            if debug:
                print(f"\n[Orchestrator] LLM signals DONE after {iteration} iterations")
            break

        # Check if no tools to run
        if not planning_result.tools:
            if debug:
                print(f"\n[Orchestrator] No tools to run, ending loop")
            break

        # Execute wave
        if debug:
            print(f"[Orchestrator] Executing wave with {len(planning_result.tools)} tools")

        wave_results = await self.runtime.execute_wave(
            tools=planning_result.tools,
            credentials=credentials,
            debug=debug
        )

        # Accumulate results
        all_results.update(wave_results)

        # Add to conversation history for next iteration
        conversation_history.append({
            "role": "assistant",
            "content": f"Executed {len(planning_result.tools)} tools: {[t.id for t in planning_result.tools]}",
            "tool_results": wave_results
        })

        iteration += 1

    if debug:
        print(f"\n{'=' * 70}")
        print(f"[Orchestrator] Execution complete after {iteration} iterations")
        print(f"{'=' * 70}\n")

    return {
        "action": final_planning_result.action if final_planning_result else "No action",
        "reasoning": final_planning_result.reasoning if final_planning_result else "",
        "slots": final_planning_result.slots.dict() if final_planning_result else {},
        "tools": [t.id for t in (final_planning_result.tools if final_planning_result else [])],
        "results": all_results,
        "iterations": iteration
    }
```

### 3. Update ToolPlanner (`agent/llm/tool_planner.py`)

Update the `plan()` method to accept conversation history and previous results:

```python
async def plan(
    self,
    message: str,
    conversation_history: List[dict] = None,
    previous_results: dict = None,
    debug: bool = False
) -> PlanningResult:
    """
    Plan NEXT wave of tools based on conversation history and previous results.

    AGENTIC LOOP MODE:
    - First call: Plan first wave based on user message
    - Subsequent calls: Plan next wave based on previous tool results
    - Returns status="done" when no more tools needed
    """

    if conversation_history is None:
        conversation_history = [{"role": "user", "content": message}]

    # Add previous results to context if available
    if previous_results:
        results_summary = "\n\n## Previous Tool Results:\n"
        for tool_id, result in previous_results.items():
            if isinstance(result, dict) and "error" not in result:
                results_summary += f"\n### {tool_id}:\n{json.dumps(result, indent=2)}\n"
            elif isinstance(result, str):
                results_summary += f"\n### {tool_id}:\n{result}\n"
            else:
                results_summary += f"\n### {tool_id}:\n{result}\n"

        # Add to last message
        conversation_history[-1]["content"] += results_summary

    # Build system prompt
    system_prompt = self._build_system_prompt()

    if debug:
        print(f"\n[ToolPlanner] Planning next wave")
        print(f"[ToolPlanner] Previous results: {list(previous_results.keys()) if previous_results else 'None'}")

    # LLM call
    result = self.llm.structured_completion(
        system_prompt=system_prompt,
        user_message=conversation_history[-1]["content"],
        response_schema=PlanningResult,
        temperature=0.0
    )

    if debug:
        print(f"[ToolPlanner] Status: {result.status}")
        print(f"[ToolPlanner] Action: {result.action}")
        print(f"[ToolPlanner] Tools ({len(result.tools)}): {[t.id for t in result.tools]}")
        print(f"[ToolPlanner] Reasoning: {result.reasoning}")

    return result
```

### 4. Update Runtime (`agent/core/runtime.py`)

Add `execute_wave()` method (simpler than current `execute()`):

```python
async def execute_wave(
    self,
    tools: List[ToolCall],
    credentials: dict,
    debug: bool = False
) -> dict:
    """
    Execute all tools in a wave (in parallel).

    Args:
        tools: List of tool calls to execute
        credentials: PMS credentials to inject
        debug: Enable debug logging

    Returns:
        Dict mapping tool_id to result
    """
    if not tools:
        return {}

    if debug:
        print(f"\n[Runtime] Executing wave with {len(tools)} tools in parallel")
        for tool in tools:
            print(f"  - {tool.id}: {tool.tool}")

    # Create tasks for each tool
    tasks = [
        self._execute_tool(tool, credentials, debug)
        for tool in tools
    ]

    # Execute all in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Package results
    wave_results = {}
    for tool, result in zip(tools, results):
        if isinstance(result, Exception):
            if debug:
                print(f"  [Runtime] {tool.id} FAILED: {result}")
            wave_results[tool.id] = {"error": str(result)}
        else:
            if debug:
                print(f"  [Runtime] {tool.id} completed")
            wave_results[tool.id] = result

    return wave_results
```

### 5. Update Planner Prompt (`prompts/planner.yaml`)

Update the system prompt to explain agentic loop mode. Key sections to add:

```yaml
## AGENTIC LOOP MODE

You work iteratively:
1. Plan NEXT tools to execute (can be multiple if independent)
2. System executes them and gives you results
3. You decide: continue with more tools OR done

## PLANNING STATUS

**status="continue"**: You need more tool calls after this wave
- Example: Need to resolve dates first, then check availability

**status="done"**: You have all info needed, this is the last wave
- Example: Already have availability data, no more tools needed
- Can also be "done" with empty tools array if you already have everything

## PARALLEL EXECUTION

If tools are independent, return them ALL in one wave:
- Example: User wants "Hanukkah and next weekend" → Both date resolutions in same wave
- Example: User wants "compare two rooms" → Both availability checks in same wave

## SEQUENTIAL EXECUTION

If you need results before planning next tool:
- Wave 1: Get dates (status="continue")
- Wave 2: Check availability with those dates (status="done")

## IMPORTANT RULES

1. **Always set status correctly**:
   - "continue" if you'll need more tools after this wave
   - "done" if this is the final wave (or no tools needed)

2. **Use previous results**:
   - Look at "Previous Tool Results" section in context
   - Extract dates, prices, etc. from previous results
   - Don't call the same tool twice

3. **Parallel when possible**:
   - Independent operations in same wave
   - Reduces latency

4. **One wave at a time**:
   - Don't plan tools for future waves
   - Only plan what to do RIGHT NOW
```

### 6. Remove Unused Code

Files/functions to remove:
- `agent/tools/calendar/tools.py` → Remove `resolve_date_with_context` function and its registration
- `agent/core/runtime.py` → Remove `_organize_into_waves()` method (no longer needed, we plan one wave at a time)
- Update all example/prompt files that mention DAG or `needs` dependencies

### 7. Update Tests

Update tests to expect multiple iterations:

```python
async def test_holiday_availability_agentic_loop():
    """Test agentic loop with holiday query"""
    orchestrator = Orchestrator.create_default()

    result = await orchestrator.process_message(
        message="one night in Hanukkah",
        pms_type="minihotel",
        pms_username="test",
        pms_password="test",
        hotel_id="test"
    )

    # Should take 2 iterations
    assert result["iterations"] == 2

    # Should have both holiday and availability results
    assert "get_holiday" in result["results"]
    assert "check_availability" in result["results"]

    # Final action should be about availability
    assert "availability" in result["action"].lower() or "check" in result["action"].lower()
```

## Testing Checklist

- [ ] Simple case: "Check availability for January 17-19" (1 wave)
- [ ] Two-wave case: "one night in Hanukkah" (2 waves: dates, then availability)
- [ ] Parallel case: "Check Hanukkah and next weekend" (Wave 1: both dates parallel, Wave 2: both availability parallel)
- [ ] FAQ case: "What rooms do you have?" (1 wave, no iterations needed)
- [ ] Complex case: "Compare availability for Hanukkah vs next weekend" (2 waves)

## Summary

**Completed**:
1. ✅ Schema updates (added `status`, removed `needs`)
2. ✅ Documentation written

**To Do**:
1. Refactor Orchestrator (add agentic loop)
2. Update ToolPlanner (accept conversation history)
3. Add Runtime.execute_wave() method
4. Update planner prompt
5. Remove unused code
6. Update tests

**Estimated Time**: 2-3 hours
**Risk**: Low (mostly adding loop logic, existing wave execution works)
