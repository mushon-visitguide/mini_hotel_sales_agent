# Step 5: Feedback Loop with Validation & Adaptation

## Goal
Implement adaptive execution with validation and automatic replanning when tool results are insufficient or unexpected.

## Context
- Current system is "one-shot" - plans all tools upfront without seeing results
- Need to validate results and adapt strategy if needed
- Should handle: no availability → try alternatives, errors → retry differently, unexpected data → adjust approach
- Must work with cancellation system from Steps 1-3
- Keep efficiency of upfront planning for successful cases (most requests)

## Requirements

### 1. Result Validation
After executing initial plan, check if results are usable:
- ✅ **Valid:** Results are good, proceed to response
- ❌ **Invalid:** Empty availability, errors, unexpected data
- 🔄 **Needs Adaptation:** Suggest alternative strategies

### 2. Adaptation Strategy
When validation fails:
1. Generate feedback on what went wrong
2. LLM replans with awareness of what failed
3. Execute adapted plan
4. Limit adaptations to prevent infinite loops (max 1-2 turns)

### 3. Integration with Cancellation
- Check cancellation token before each phase
- Support cancellation during adaptation
- Preserve partial results when cancelled

## Files to Examine
- `agent/core/orchestrator.py` - Main execution flow
- `agent/llm/planner.py` - Tool planning (needs adapt() method)
- `agent/core/runtime.py` - Tool execution
- `prompts/planner.yaml` - Current planning prompt

## Deliverables

### 1. Result Validator
**Create `agent/core/validator.py`:**

```python
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ValidationIssue:
    """Specific issue found in results"""
    type: str  # 'error', 'no_availability', 'unexpected_data'
    tool_id: str
    message: str
    severity: str  # 'critical', 'warning'


@dataclass
class ValidationResult:
    """Result of validating tool execution results"""
    is_valid: bool
    needs_adaptation: bool
    issues: List[ValidationIssue]
    feedback: Optional[str]  # Human-readable feedback for replanning
    suggestions: List[str]  # Suggested alternative strategies


class ResultValidator:
    """
    Validates tool execution results and determines if adaptation is needed.

    Checks for:
    - Explicit errors in results
    - Empty/null results where data expected
    - No availability when searching rooms
    - Unexpected data formats
    """

    def __init__(self):
        self.max_retries_per_issue = 1  # Don't retry same issue forever
        self.issue_history: Dict[str, int] = {}  # Track retry attempts

    async def validate(
        self,
        plan: PlanningResult,
        results: Dict[str, Any],
        turn_number: int = 0,
        max_turns: int = 2
    ) -> ValidationResult:
        """
        Validate tool execution results.

        Args:
            plan: Original planning result
            results: Tool execution results
            turn_number: Current adaptation turn (0 = initial)
            max_turns: Maximum adaptation turns allowed

        Returns:
            ValidationResult with issues and suggestions
        """
        issues = []

        # Don't adapt on final turn
        if turn_number >= max_turns:
            return ValidationResult(
                is_valid=True,  # Accept what we have
                needs_adaptation=False,
                issues=[],
                feedback="Max adaptation turns reached",
                suggestions=[]
            )

        # Check for explicit errors
        for tool_id, result in results.items():
            if isinstance(result, dict) and "error" in result:
                issue_key = f"error:{tool_id}"
                attempts = self.issue_history.get(issue_key, 0)

                if attempts < self.max_retries_per_issue:
                    self.issue_history[issue_key] = attempts + 1
                    issues.append(ValidationIssue(
                        type='error',
                        tool_id=tool_id,
                        message=result['error'],
                        severity='critical'
                    ))

        # Check for empty availability results
        availability_results = [
            (tid, r) for tid, r in results.items()
            if 'availability' in tid.lower()
        ]

        for tool_id, result in availability_results:
            if isinstance(result, dict):
                rooms = result.get('available_rooms', [])
                if not rooms or len(rooms) == 0:
                    issue_key = "no_availability"
                    attempts = self.issue_history.get(issue_key, 0)

                    # Only try alternatives once for no availability
                    if attempts < 1:
                        self.issue_history[issue_key] = attempts + 1
                        issues.append(ValidationIssue(
                            type='no_availability',
                            tool_id=tool_id,
                            message='No rooms available for requested dates',
                            severity='warning'
                        ))

        # Check for unexpected null/empty critical data
        # e.g., calendar tool should return dates
        calendar_results = [
            (tid, r) for tid, r in results.items()
            if 'calendar' in tid.lower()
        ]

        for tool_id, result in calendar_results:
            if isinstance(result, dict):
                if not result.get('check_in') or not result.get('check_out'):
                    issues.append(ValidationIssue(
                        type='unexpected_data',
                        tool_id=tool_id,
                        message='Calendar tool did not return expected dates',
                        severity='critical'
                    ))

        # Determine if adaptation is needed
        needs_adaptation = len(issues) > 0

        # Generate feedback and suggestions
        feedback = self._generate_feedback(issues) if issues else None
        suggestions = self._generate_suggestions(issues, plan, results)

        return ValidationResult(
            is_valid=not needs_adaptation,
            needs_adaptation=needs_adaptation,
            issues=issues,
            feedback=feedback,
            suggestions=suggestions
        )

    def _generate_feedback(self, issues: List[ValidationIssue]) -> str:
        """Generate human-readable feedback for replanning"""
        feedback_parts = ["Issues found with initial plan:"]

        for issue in issues:
            if issue.type == 'error':
                feedback_parts.append(f"- {issue.tool_id} failed: {issue.message}")
            elif issue.type == 'no_availability':
                feedback_parts.append(f"- No rooms available for requested dates")
            elif issue.type == 'unexpected_data':
                feedback_parts.append(f"- {issue.message}")

        return "\n".join(feedback_parts)

    def _generate_suggestions(
        self,
        issues: List[ValidationIssue],
        plan: PlanningResult,
        results: Dict[str, Any]
    ) -> List[str]:
        """Generate specific suggestions for adaptation"""
        suggestions = []

        for issue in issues:
            if issue.type == 'no_availability':
                # Extract dates from results to suggest alternatives
                dates = self._extract_dates(results)
                if dates:
                    suggestions.append(f"Try nearby dates: day before/after {dates['check_in']}")
                    suggestions.append(f"Try shorter stay duration (1-2 nights)")
                else:
                    suggestions.append("Try different date range")

            elif issue.type == 'error':
                if 'timeout' in issue.message.lower():
                    suggestions.append(f"Retry {issue.tool_id} with longer timeout")
                else:
                    suggestions.append(f"Try alternative tool or approach for {issue.tool_id}")

        return suggestions

    def _extract_dates(self, results: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Extract dates from results for suggestions"""
        for result in results.values():
            if isinstance(result, dict):
                if 'check_in' in result and 'check_out' in result:
                    return {
                        'check_in': result['check_in'],
                        'check_out': result['check_out']
                    }
        return None

    def reset(self):
        """Reset issue history for new request"""
        self.issue_history.clear()
```

### 2. Planner Adaptation Method
**Add to `agent/llm/planner.py`:**

```python
class ToolPlanner:
    async def adapt(
        self,
        original_message: str,
        original_plan: PlanningResult,
        original_results: Dict[str, Any],
        validation: ValidationResult,
        attempted_tools: Set[str]
    ) -> PlanningResult:
        """
        Re-plan based on validation feedback.

        Args:
            original_message: User's original message
            original_plan: Initial planning result
            original_results: Results from initial execution
            validation: Validation result with issues and suggestions
            attempted_tools: Set of tool signatures already tried

        Returns:
            New planning result with alternative approach
        """

        # Build context for adaptation
        context = self._build_adaptation_context(
            original_message,
            original_plan,
            original_results,
            validation,
            attempted_tools
        )

        # Create adapted plan
        adapted_plan = await self.plan(
            message=context,
            context=None  # Context is in the message
        )

        return adapted_plan

    def _build_adaptation_context(
        self,
        original_message: str,
        original_plan: PlanningResult,
        original_results: Dict[str, Any],
        validation: ValidationResult,
        attempted_tools: Set[str]
    ) -> str:
        """Build rich context for adaptation planning"""

        context_parts = [
            "# Adaptation Context",
            "",
            "## Original User Request",
            original_message,
            "",
            "## What We Tried",
            f"Action: {original_plan.action}",
            "Tools executed:",
        ]

        # Show what tools were executed
        for tool in original_plan.tools:
            context_parts.append(f"- {tool.tool} (ID: {tool.id})")

        context_parts.extend([
            "",
            "## What Happened",
        ])

        # Summarize results
        for tool in original_plan.tools:
            result = original_results.get(tool.id)
            summary = self._summarize_result(result)
            context_parts.append(f"- {tool.tool}: {summary}")

        context_parts.extend([
            "",
            "## Issues Identified",
            validation.feedback or "No specific issues",
            "",
            "## Suggestions",
        ])

        for suggestion in validation.suggestions:
            context_parts.append(f"- {suggestion}")

        context_parts.extend([
            "",
            "## Already Attempted",
            "Do NOT repeat these exact tool calls:",
        ])

        for tool_sig in attempted_tools:
            context_parts.append(f"- {tool_sig}")

        context_parts.extend([
            "",
            "## Your Task",
            "Plan ALTERNATIVE tools to try based on the issues and suggestions above.",
            "",
            "IMPORTANT:",
            "- Use DIFFERENT approaches than what we already tried",
            "- If no availability for dates X, try dates Y (nearby)",
            "- If tool failed, try alternative tool or different parameters",
            "- If nothing reasonable to try, return EMPTY tools list",
            "",
            "Return your plan with tools that have a good chance of success.",
            "If you believe we should respond with current results (no good alternatives), return empty tools list.",
        ])

        return "\n".join(context_parts)

    def _summarize_result(self, result: Any) -> str:
        """Summarize result for context"""
        if isinstance(result, dict):
            if "error" in result:
                return f"❌ ERROR: {result['error']}"
            elif "available_rooms" in result:
                rooms = result.get("available_rooms", [])
                if not rooms:
                    return "❌ No rooms available"
                return f"✅ Found {len(rooms)} rooms"
            elif "check_in" in result:
                return f"✅ Dates: {result['check_in']} to {result['check_out']}"
        return "✅ Success"
```

### 3. Orchestrator with Feedback Loop
**Update `agent/core/orchestrator.py`:**

```python
class Orchestrator:
    MAX_ADAPTATION_TURNS = 1  # Allow 1 adaptation (2 total attempts)
    MAX_TOTAL_TOOLS = 10  # Prevent tool spam

    def __init__(self, ...):
        # ... existing init ...
        self.validator = ResultValidator()

    async def process_message(
        self,
        message: str,
        user_id: str,
        cancel_token: Optional[CancellationToken] = None,
        send_progress: Optional[Callable] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Process message with feedback loop and adaptation"""

        # Reset validator for new request
        self.validator.reset()

        # Track what we've tried
        attempted_tools = set()
        all_results = {}
        total_tools_executed = 0

        # Check cancellation
        if cancel_token and cancel_token.is_cancelled:
            raise CancelledException("Cancelled before start")

        # PHASE 1: Initial Planning
        initial_plan = await self.planner.plan(message)

        # Check cancellation
        if cancel_token and cancel_token.is_cancelled:
            raise CancelledException("Cancelled during planning")

        # PHASE 2: Execute Initial Plan
        results = await self.runtime.execute(
            initial_plan.tools,
            credentials=kwargs,
            cancel_token=cancel_token
        )

        all_results.update(results)

        # Track attempts
        for tool in initial_plan.tools:
            sig = self._get_tool_signature(tool)
            attempted_tools.add(sig)
            total_tools_executed += 1

        # Check cancellation
        if cancel_token and cancel_token.is_cancelled:
            raise CancelledException("Cancelled during execution")

        # PHASE 3: Validation & Adaptation Loop
        for turn in range(self.MAX_ADAPTATION_TURNS):
            # Validate results
            validation = await self.validator.validate(
                plan=initial_plan,
                results=all_results,
                turn_number=turn,
                max_turns=self.MAX_ADAPTATION_TURNS
            )

            # Check if adaptation needed
            if not validation.needs_adaptation:
                logger.info("Results are valid, no adaptation needed")
                break

            # Check if we've hit limits
            if total_tools_executed >= self.MAX_TOTAL_TOOLS:
                logger.warning(f"Hit max tools limit ({self.MAX_TOTAL_TOOLS}), stopping")
                break

            # Check cancellation
            if cancel_token and cancel_token.is_cancelled:
                raise CancelledException("Cancelled before adaptation")

            # Notify user of adaptation
            if send_progress:
                await send_progress(
                    user_id,
                    "🔄 Trying alternatives..."
                )

            # Get adapted plan
            adapted_plan = await self.planner.adapt(
                original_message=message,
                original_plan=initial_plan,
                original_results=all_results,
                validation=validation,
                attempted_tools=attempted_tools
            )

            # Check if planner gave up
            if not adapted_plan.tools:
                logger.info("Planner returned no new tools, stopping adaptation")
                break

            # Filter out duplicates
            new_tools = []
            for tool in adapted_plan.tools:
                sig = self._get_tool_signature(tool)

                if sig in attempted_tools:
                    logger.warning(f"Skipping duplicate tool: {tool.tool}")
                    continue

                if total_tools_executed + len(new_tools) + 1 > self.MAX_TOTAL_TOOLS:
                    logger.warning("Would exceed max tools, stopping")
                    break

                attempted_tools.add(sig)
                new_tools.append(tool)

            if not new_tools:
                logger.info("No valid new tools after filtering")
                break

            # Check cancellation
            if cancel_token and cancel_token.is_cancelled:
                raise CancelledException("Cancelled during adaptation")

            # Execute adapted tools
            logger.info(f"Adaptation turn {turn + 1}: executing {len(new_tools)} tools")
            additional = await self.runtime.execute(
                new_tools,
                credentials=kwargs,
                cancel_token=cancel_token
            )

            all_results.update(additional)
            total_tools_executed += len(new_tools)

        # PHASE 4: Generate Response
        response = await self.responder.generate(
            user_message=message,
            results=all_results
        )

        return {
            "response": response,
            "results": all_results,
            "tools_executed": total_tools_executed,
            "adaptation_turns": turn + 1 if 'turn' in locals() else 0
        }

    def _get_tool_signature(self, tool: ToolCall) -> str:
        """Create signature to detect duplicate tool calls"""
        key_args = {
            k: v for k, v in (tool.args or {}).items()
            if k in ['check_in', 'check_out', 'adults', 'date_hint']
        }
        return f"{tool.tool}:{hash(frozenset(key_args.items()))}"
```

## Implementation Notes

### Safeguards Against Infinite Loops
1. **Max adaptation turns** = 1 (total 2 attempts: initial + 1 adaptation)
2. **Max total tools** = 10 (prevent tool spam)
3. **Track attempted tools** (don't repeat same call)
4. **Validator tracks retries** (max 1 retry per issue type)
5. **Always respond** (even if adaptation fails)

### Adaptation Examples

**Example 1: No Availability**
```
Turn 0: availability(Dec 25) → []
Validation: "No rooms for Dec 25"
Suggestions: "Try Dec 24 or Dec 26"
Turn 1: availability(Dec 24), availability(Dec 26) → [rooms on Dec 26]
Response: "Dec 25 is full, but Dec 26 has rooms!"
```

**Example 2: 8-Night Hanukkah**
```
Turn 0: calendar → "8 nights", availability(8 nights) → []
Validation: "No rooms for 8 nights"
Suggestions: "Try shorter stay (2-3 nights)"
Turn 1: availability(2 nights) → [rooms found]
Response: "Full 8 nights unavailable, but weekend stay available!"
```

## Success Criteria
- Handles no availability by trying alternatives
- Handles errors by retrying differently
- Respects max turns (no infinite loops)
- Works with cancellation system
- Preserves efficiency for successful cases (1 LLM call if results are good)
- Logs adaptation via hooks for monitoring

## Testing Scenarios
1. **Success case** - No adaptation needed
2. **No availability** - Tries nearby dates
3. **Tool error** - Retries with different approach
4. **Max turns reached** - Responds with best available data
5. **Cancelled during adaptation** - Raises CancelledException gracefully
6. **Duplicate prevention** - Doesn't retry exact same tool call

## Monitoring
```python
# Emit events for tracking
await runtime_events.emit(
    'validation_complete',
    needs_adaptation=validation.needs_adaptation,
    issues=len(validation.issues)
)

await runtime_events.emit(
    'adaptation_started',
    turn=turn,
    reason=validation.feedback
)

await runtime_events.emit(
    'adaptation_complete',
    turn=turn,
    tools_executed=len(new_tools),
    success=True
)
```
