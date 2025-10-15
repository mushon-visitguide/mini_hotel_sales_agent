# 🔄 Agentic Loop Architecture - Claude-Style Tool Execution

**Date**: January 2025
**Status**: ✅ Active Architecture

---

## Overview

The agent uses an **iterative agentic loop** inspired by Claude's tool-use pattern. Instead of planning all tools upfront (DAG), the LLM plans and executes tools **one wave at a time**, using previous results to inform the next wave.

---

## Key Principle: Sequential Planning with Parallel Execution

```
User: "I need availability for Hanukkah and also next weekend"

WAVE 1 (Parallel Date Resolution):
  LLM Plans → calendar.resolve_holiday("Hanukkah")
           → calendar.resolve_date_hint("next weekend")
  Execute → "Hanukkah is from 2026-12-04 to 2026-12-11"
           → "Next weekend is 2025-01-17 to 2025-01-19"

WAVE 2 (LLM Re-plans with new info):
  LLM sees both date results
  LLM Plans → pms.get_availability(check_in="2026-12-04", check_out="2026-12-05")
           → pms.get_availability(check_in="2025-01-17", check_out="2025-01-19")
  Execute → Returns availability for both date ranges in parallel

DONE: LLM has all info, returns final response
```

---

## Architecture Flow

### Current (OLD) - Upfront DAG Planning ❌
```
User Message
  → LLM plans ALL tools upfront (DAG with dependencies)
  → Runtime executes waves based on DAG
  → Return results
```

**Problem**: LLM doesn't know tool results when planning next tools.

**Example Failure**:
```python
# LLM tries to plan everything at once:
tools = [
    {"id": "get_holiday", "tool": "calendar.resolve_holiday", "args": {"holiday_name": "Hanukkah"}},
    {"id": "check_avail", "tool": "pms.get_availability", "args": {"check_in": ???, "check_out": ???}}
    # ^^^ Can't fill dates because holiday tool hasn't run yet!
]
```

---

### New (AGENTIC LOOP) - Iterative Planning ✅
```
User Message
  ↓
Loop:
  1. LLM plans NEXT WAVE of tools (based on previous results)
  2. Runtime executes wave in parallel
  3. Return results to LLM
  4. If LLM says "continue" → go to step 1
  5. If LLM says "done" → compose final response
  ↓
Final Response
```

**Example Success**:
```python
# Wave 1: LLM plans first tools
wave_1 = [
    {"id": "get_holiday", "tool": "calendar.resolve_holiday", "args": {"holiday_name": "Hanukkah"}}
]
# Execute → "Hanukkah is from 2026-12-04 to 2026-12-11"

# Wave 2: LLM sees result, plans next tool
wave_2 = [
    {"id": "check_avail", "tool": "pms.get_availability",
     "args": {"check_in": "2026-12-04", "check_out": "2026-12-05"}}  # ✅ Dates known!
]
```

---

## Implementation Changes

### 1. Orchestrator - Agentic Loop Controller

**File**: `agent/core/orchestrator.py`

```python
async def process_message(self, message: str, **credentials) -> dict:
    """
    Agentic loop: Plan → Execute → Re-plan → Execute → ... → Done
    """
    conversation_history = [{"role": "user", "content": message}]
    all_results = {}
    iteration = 0
    max_iterations = 5  # Safety limit

    while iteration < max_iterations:
        # LLM plans NEXT wave based on conversation history
        planning_result = await self.tool_planner.plan_next_wave(
            conversation_history=conversation_history,
            previous_results=all_results
        )

        if planning_result.status == "done":
            # LLM has all info needed
            break

        if not planning_result.tools:
            # No tools to run
            break

        # Execute wave (tools run in parallel)
        wave_results = await self.runtime.execute_wave(
            tools=planning_result.tools,
            credentials=credentials
        )

        # Add results to history for LLM
        all_results.update(wave_results)
        conversation_history.append({
            "role": "assistant",
            "content": f"Executed {len(planning_result.tools)} tools",
            "tool_results": wave_results
        })

        iteration += 1

    # LLM composes final response
    return {
        "action": planning_result.action,
        "reasoning": planning_result.reasoning,
        "results": all_results,
        "iterations": iteration
    }
```

---

### 2. ToolPlanner - Wave-by-Wave Planning

**File**: `agent/llm/tool_planner.py`

```python
async def plan_next_wave(
    self,
    conversation_history: List[dict],
    previous_results: dict
) -> PlanningResult:
    """
    LLM decides:
    1. What tools to run NEXT (in parallel if independent)
    2. Whether to continue or if done

    Returns:
        PlanningResult with:
        - status: "continue" | "done"
        - tools: List of tools to run in parallel (empty if done)
        - reasoning: Why these tools
    """
    system_prompt = self._load_prompt("planner.yaml")

    # Add previous results to context
    if previous_results:
        context = f"\nPrevious tool results:\n{json.dumps(previous_results, indent=2)}"
        conversation_history[-1]["content"] += context

    # LLM call with structured output
    result = self.llm.structured_completion(
        system_prompt=system_prompt,
        messages=conversation_history,
        response_schema=PlanningResult,
        temperature=0.0
    )

    return result
```

---

### 3. Runtime - Wave Executor (No Changes Needed!)

**File**: `agent/core/runtime.py`

The runtime already supports wave execution. No changes needed - it just runs one wave at a time now instead of organizing a full DAG.

```python
async def execute_wave(
    self,
    tools: List[ToolCall],
    credentials: dict
) -> dict:
    """
    Execute all tools in parallel (they're in same wave)
    """
    tasks = [
        self._execute_tool(tool, credentials)
        for tool in tools
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    return {
        tool.id: result if not isinstance(result, Exception) else {"error": str(result)}
        for tool, result in zip(tools, results)
    }
```

---

### 4. Prompt Updates - Iterative Instructions

**File**: `prompts/planner.yaml`

```yaml
system_prompt: |
  You are a tool planner for a hotel booking assistant.

  ## AGENTIC LOOP MODE
  You work iteratively:
  1. Plan NEXT tools to execute (can be multiple if independent)
  2. System executes them and gives you results
  3. You decide: continue with more tools OR done

  ## PLANNING RULES

  **Parallel Execution**:
  - If tools are independent, return them ALL in one wave
  - Example: Resolving "Hanukkah dates" and "next weekend dates" → Both in same wave

  **Sequential Execution**:
  - If you need tool results before planning next tool, return status="continue"
  - Example: Need holiday dates before checking availability → Wave 1: get dates, Wave 2: check availability

  **Completion**:
  - When you have all info needed, return status="done" with empty tools array

  ## OUTPUT SCHEMA
  {
    "status": "continue" | "done",
    "action": "Natural language description of what you're doing",
    "tools": [
      {"id": "unique_id", "tool": "tool.name", "args": {...}, "needs": []}
    ],
    "reasoning": "Why these tools / why done"
  }

  ## EXAMPLE: Holiday Availability

  **Wave 1**:
  User: "Check availability for Hanukkah"
  Output: {
    "status": "continue",
    "action": "Getting Hanukkah dates",
    "tools": [{"id": "get_holiday", "tool": "calendar.resolve_holiday", "args": {"holiday_name": "Hanukkah"}}],
    "reasoning": "Need to resolve holiday dates before checking availability"
  }

  **Wave 2** (after getting "Hanukkah is from 2026-12-04 to 2026-12-11"):
  Output: {
    "status": "done",
    "action": "Check availability for Hanukkah",
    "tools": [{"id": "check_avail", "tool": "pms.get_availability", "args": {"check_in": "2026-12-04", "check_out": "2026-12-05", ...}}],
    "reasoning": "Have all dates, checking availability. Will be done after this."
  }
```

---

## Benefits of Agentic Loop

### ✅ Advantages

1. **Dynamic Decision Making**
   - LLM can see tool results before planning next tools
   - No need to guess arguments

2. **Parallel Execution Preserved**
   - Independent tools still run in parallel within each wave
   - Example: Multiple date resolutions, multiple availability checks

3. **Simpler Mental Model**
   - No complex DAG dependencies
   - Just: "What should I do next?"

4. **Matches Claude's Approach**
   - Proven pattern used by Anthropic
   - Well-documented and understood

5. **Error Recovery**
   - LLM can adjust plan if tool fails
   - Can try alternative approaches

### ⚠️ Trade-offs

1. **More LLM Calls**
   - One LLM call per wave instead of one upfront
   - Mitigated by: Fast tools, parallel execution within waves

2. **Slightly Higher Latency**
   - LLM call overhead between waves
   - Mitigated by: GPT-4 is fast (~500ms), parallel execution

---

## Example Scenarios

### Scenario 1: Simple Holiday Query
```
User: "one night in Hanukkah"

Wave 1:
  LLM: "I need Hanukkah dates"
  Tools: [calendar.resolve_holiday("Hanukkah")]
  Result: "Hanukkah is from 2026-12-04 to 2026-12-11"

Wave 2:
  LLM: "Now I can check availability"
  Tools: [pms.get_availability(check_in="2026-12-04", check_out="2026-12-05")]
  Result: [Room data...]

Wave 3:
  LLM: "Done, I have all info"
  Status: "done"
```

**Total**: 2 tool waves, 3 LLM calls

---

### Scenario 2: Multiple Date Ranges
```
User: "Check availability for Hanukkah and also next weekend"

Wave 1:
  LLM: "I need both date ranges - can resolve in parallel"
  Tools: [
    calendar.resolve_holiday("Hanukkah"),
    calendar.resolve_date_hint("next weekend")
  ]
  Results:
    - "Hanukkah is from 2026-12-04 to 2026-12-11"
    - "Next weekend is 2025-01-17 to 2025-01-19"

Wave 2:
  LLM: "Now check availability for both - can run in parallel"
  Tools: [
    pms.get_availability(check_in="2026-12-04", check_out="2026-12-05"),
    pms.get_availability(check_in="2025-01-17", check_out="2025-01-19")
  ]
  Results: [Room data for both...]

Wave 3:
  LLM: "Done, I have all info"
  Status: "done"
```

**Total**: 2 tool waves, 3 LLM calls

---

### Scenario 3: Already Have Dates
```
User: "Check availability for January 17-19"

Wave 1:
  LLM: "I have dates, can check availability directly"
  Tools: [pms.get_availability(check_in="2025-01-17", check_out="2025-01-19")]
  Result: [Room data...]

Wave 2:
  LLM: "Done, I have all info"
  Status: "done"
```

**Total**: 1 tool wave, 2 LLM calls

---

## Schema Updates

### PlanningResult (Updated)

```python
class PlanningResult(BaseModel):
    """Result from LLM tool planning - ONE WAVE AT A TIME"""
    status: Literal["continue", "done"] = Field(
        description="Whether to continue with more tools or done"
    )
    action: str = Field(
        description="Natural language description of current action"
    )
    slots: Slots = Field(
        description="Extracted parameters from user message"
    )
    tools: List[ToolCall] = Field(
        default_factory=list,
        description="Tools to execute in THIS wave (empty if done)"
    )
    reasoning: str = Field(
        description="Why these tools or why done"
    )
```

---

## Migration Strategy

### Phase 1: Update Schemas ✅
- Add `status` field to `PlanningResult`
- Update prompt to explain agentic loop

### Phase 2: Refactor Orchestrator ✅
- Change from single `plan()` call to loop with `plan_next_wave()`
- Track conversation history
- Accumulate results across waves

### Phase 3: Update Tool Planner ✅
- Change method from `plan()` to `plan_next_wave()`
- Accept conversation history + previous results
- Return one wave at a time

### Phase 4: Keep Runtime As-Is ✅
- Runtime already supports wave execution
- Just call `execute_wave()` instead of `execute(full_dag)`

### Phase 5: Testing ✅
- Test simple cases (1 wave)
- Test multi-wave cases (holiday → availability)
- Test parallel waves (multiple date resolutions)

---

## Code Changes Summary

### Files to Modify:
1. `agent/core/orchestrator.py` - Add agentic loop
2. `agent/llm/tool_planner.py` - Change to `plan_next_wave()`
3. `agent/llm/schemas.py` - Add `status` field
4. `prompts/planner.yaml` - Update instructions for iterative planning

### Files to Keep:
1. `agent/core/runtime.py` - Already supports waves, no changes needed
2. `agent/tools/*` - No changes needed
3. All tool implementations - No changes needed

### Files to Remove:
1. `calendar.resolve_date_with_context` - No longer needed, LLM handles this logic

---

## Testing Plan

### Unit Tests:
```python
async def test_agentic_loop_single_wave():
    """Test case where everything happens in one wave"""
    message = "Check availability for January 17-19"
    # Should execute: [pms.get_availability]
    # Then: status="done"

async def test_agentic_loop_two_waves():
    """Test case needing two waves"""
    message = "one night in Hanukkah"
    # Wave 1: [calendar.resolve_holiday]
    # Wave 2: [pms.get_availability]
    # Then: status="done"

async def test_agentic_loop_parallel_resolution():
    """Test parallel date resolution"""
    message = "Check Hanukkah and next weekend"
    # Wave 1: [resolve_holiday, resolve_date_hint] (parallel)
    # Wave 2: [get_availability, get_availability] (parallel)
    # Then: status="done"
```

### Integration Tests:
- Run through all existing test conversations
- Verify same results as before
- Check iteration counts reasonable (< 5 waves)

---

## Performance Characteristics

### Latency Analysis:

**OLD (Upfront DAG)**:
```
LLM Planning: 500ms
Wave 1 (parallel): 200ms
Wave 2 (depends on wave 1): 300ms
Total: ~1000ms
```

**NEW (Agentic Loop - 2 Waves)**:
```
LLM Planning Wave 1: 500ms
Wave 1 Execution: 200ms
LLM Planning Wave 2: 500ms
Wave 2 Execution: 300ms
Total: ~1500ms
```

**Trade-off**: +500ms for multi-wave scenarios, but much more flexible and correct.

---

## Success Criteria

- ✅ "one night in Hanukkah" resolves correctly (2 waves)
- ✅ "Check Hanukkah and next weekend" executes dates in parallel
- ✅ Simple queries still work (1 wave)
- ✅ All existing tests pass
- ✅ Iteration count < 5 for all test cases
- ✅ No degradation in simple cases

---

## Rollout

1. **Feature Flag**: Add `AGENTIC_LOOP_ENABLED` flag
2. **A/B Test**: Run 10% traffic on new architecture
3. **Monitor**: Track iteration counts, latency, success rates
4. **Full Rollout**: Once validated, make default
5. **Cleanup**: Remove old DAG planning code

---

## Future Enhancements

1. **LLM Caching**: Cache tool planning for common patterns
2. **Predictive Planning**: Anticipate next wave while executing current
3. **Parallel Replanning**: Generate multiple candidate next waves
4. **Self-Correction**: LLM can retry failed tools with different args

---

**Status**: Ready for implementation ✅
**Estimated Effort**: 4-6 hours
**Risk Level**: Low (mostly refactoring orchestrator)
