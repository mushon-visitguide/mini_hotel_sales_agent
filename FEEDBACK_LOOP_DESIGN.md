# Feedback Loop Design - Making Your System Adaptive

## The Core Problem

### Your Current System (One-Shot)

```python
User: "Book room for Hanukkah"
    ↓
Planner: Plans ALL tools upfront (blind planning)
    - calendar.resolve_date_hint("Hanukkah")
    - pms.get_availability(check_in=???, check_out=???)  # Doesn't know dates yet!
    ↓
Runtime: Executes tools
    - calendar → "8 nights: Dec 14-22"
    - availability(8 nights) → [] (no availability)
    ↓
Responder: "No rooms available for Hanukkah"
    ↓
❌ DONE - Can't try alternatives
```

**Problems:**
1. ❌ Planner doesn't see tool results
2. ❌ Can't adapt if tools return unexpected data
3. ❌ Can't try alternatives when first attempt fails
4. ❌ Can't make decisions based on intermediate results

---

## Gemini CLI's Approach (Iterative Loop)

```python
User: "Book room for Hanukkah"
    ↓
Turn 1: LLM with conversation history
    LLM: "I'll check what dates Hanukkah falls on"
    Tool calls: [calendar.resolve_date_hint("Hanukkah")]
    ↓
Execute: calendar → "8 nights: Dec 14-22"
    ↓
Add to history: Tool result with dates
    ↓
Turn 2: LLM sees previous results in history
    LLM: "8 nights is unusual for a booking. Let me check 2 nights first"
    Tool calls: [pms.get_availability(Dec 14-16, 2 nights)]
    ↓
Execute: availability → [Room A, Room B available]
    ↓
Turn 3: LLM sees availability results
    LLM: "Great! I found rooms. Here are your options..."
    Tool calls: [] (no more tools needed)
    ↓
✅ DONE - Adapted based on intermediate results
```

**Benefits:**
1. ✅ LLM sees all previous tool results
2. ✅ Can adapt strategy based on what it learns
3. ✅ Can try alternatives if first attempt fails
4. ✅ Makes smart decisions using intermediate data

---

## Real-World Examples

### Example 1: No Availability

**Current System (Yours):**
```
User: "Check availability December 25"
Planner: [check_availability(Dec 25)]
Execute: Returns [] (no rooms)
Response: "No rooms available on December 25"
❌ Stops - user gets unhelpful response
```

**With Feedback Loop:**
```
User: "Check availability December 25"

Turn 1:
  LLM → [check_availability(Dec 25)]
  Result: [] (no rooms)

Turn 2:
  LLM sees empty result → "Let me check nearby dates"
  LLM → [check_availability(Dec 24), check_availability(Dec 26)]
  Result: Dec 24 full, Dec 26 has rooms

Turn 3:
  LLM → "December 25 is fully booked, but I found availability on December 26! Would you like to see those options?"
✅ Helpful response with alternatives
```

### Example 2: Hanukkah Booking

**Current System:**
```
User: "Book Hanukkah"
Planner: [calendar("Hanukkah"), availability(???)]
Execute: Calendar says 8 nights, availability search might fail or return wrong results
Response: Based on whatever came back
❌ No adaptation
```

**With Feedback Loop:**
```
User: "Book Hanukkah"

Turn 1:
  LLM → [calendar.resolve_date_hint("Hanukkah")]
  Result: "8 nights: December 14-22, 2025"

Turn 2:
  LLM sees 8 nights → "That's the full holiday, but guests usually book 2-3 nights. Let me check a weekend stay"
  LLM → [availability(Dec 14-16, 2 nights)]
  Result: [Room A: 1200/night, Room B: 1500/night]

Turn 3:
  LLM → "Hanukkah runs December 14-22. I checked availability for a weekend stay (Dec 14-16) and found 2 great options..."
✅ Smart interpretation + helpful results
```

### Example 3: Multi-Room Request

**Current System:**
```
User: "I need 3 rooms for a family reunion"
Planner: [availability(rooms=3)] ← Plans for 3 rooms upfront
Execute: Might not find 3 identical rooms
Response: Whatever came back
❌ No fallback strategy
```

**With Feedback Loop:**
```
User: "I need 3 rooms for a family reunion"

Turn 1:
  LLM → [availability(check_in, check_out, adults=2)] # Check what's available first
  Result: [Room A x2 available, Room B x1 available, Room C x2 available]

Turn 2:
  LLM sees inventory → "Great, I can mix rooms to get 3 total"
  LLM → Already has the data, no more tools needed

Turn 3:
  LLM → "I found 3 rooms for your family reunion: 2x Room A and 1x Room B. This gives you flexibility for different family sizes..."
✅ Smart combination based on actual inventory
```

### Example 4: Price Range Filter

**Current System:**
```
User: "Show me rooms under 1000 NIS"
Planner: [availability(budget_max=1000)] ← Planner sets budget filter
Execute: PMS doesn't support budget filter, returns all rooms
Response: Shows expensive rooms too
❌ Can't post-filter because responder doesn't have filtering logic
```

**With Feedback Loop:**
```
User: "Show me rooms under 1000 NIS"

Turn 1:
  LLM → [get_availability()] # Get all rooms
  Result: [Room A: 800/night, Room B: 1200/night, Room C: 900/night]

Turn 2:
  LLM sees prices → Filters mentally: "Rooms A and C are under budget"
  No more tools needed

Turn 3:
  LLM → "I found 2 rooms under 1000 NIS: Room A (800/night) and Room C (900/night). Room B at 1200/night is just slightly over if you're flexible..."
✅ Smart filtering based on results
```

---

## Implementation Options

### Option A: Simple Validation + Retry (Easiest)

**Add result validation layer:**

```python
class Orchestrator:
    async def process_message(self, message, max_retries=1):
        """Process with simple retry on failure"""

        for attempt in range(max_retries + 1):
            # Step 1: Plan
            plan = await self.planner.plan(message)

            # Step 2: Execute
            results = await self.runtime.execute(plan.tools)

            # Step 3: Validate results
            validation = self.validate_results(results)

            if validation.is_valid or attempt == max_retries:
                # Success or out of retries
                break

            # Step 4: Re-plan with error context
            message = self.augment_message_with_errors(message, validation.errors)

        # Step 5: Generate response
        response = await self.responder.generate(results)
        return response

    def validate_results(self, results):
        """Check if results are usable"""
        errors = []

        for tool_id, result in results.items():
            # Check for explicit errors
            if isinstance(result, dict) and "error" in result:
                errors.append(f"{tool_id}: {result['error']}")

            # Check for empty results (no availability)
            if tool_id.startswith("availability") and isinstance(result, dict):
                if not result.get("available_rooms"):
                    errors.append(f"{tool_id}: No rooms available")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
```

**Pros:** Simple, catches obvious failures
**Cons:** Just retries same plan, doesn't adapt strategy

---

### Option B: Iterative Execution (Like Gemini CLI)

**Full feedback loop with conversation history:**

```python
class Orchestrator:
    async def process_message(self, message, max_turns=3):
        """Process with full feedback loop"""

        # Initialize conversation history for this request
        turn_history = []

        for turn in range(1, max_turns + 1):
            # Step 1: Plan next action based on what we learned so far
            plan = await self.planner.plan_turn(
                user_message=message,
                turn_history=turn_history,
                turn_number=turn
            )

            # Check if planner says we're done
            if not plan.tools:
                break

            # Step 2: Execute tools
            results = await self.runtime.execute(plan.tools)

            # Step 3: Add to turn history
            turn_history.append({
                'turn': turn,
                'plan': plan,
                'tool_results': results
            })

            # Step 4: Check if we should continue
            should_continue = await self.planner.should_continue(
                user_message=message,
                turn_history=turn_history
            )

            if not should_continue:
                break

        # Step 5: Generate final response based on all turns
        response = await self.responder.generate_from_turns(
            user_message=message,
            turn_history=turn_history
        )

        return response
```

**Changes needed in Planner:**

```python
# New planner method for iterative planning
async def plan_turn(
    self,
    user_message: str,
    turn_history: List[Dict],
    turn_number: int
) -> PlanningResult:
    """Plan next turn based on previous results"""

    # Build context from previous turns
    context_parts = [f"## User Request\n{user_message}\n"]

    if turn_history:
        context_parts.append("## What We've Done So Far")
        for turn in turn_history:
            context_parts.append(f"\n### Turn {turn['turn']}")
            context_parts.append(f"Action: {turn['plan'].action}")

            # Show tool results
            for tool_call in turn['plan'].tools:
                tool_id = tool_call.id
                result = turn['tool_results'].get(tool_id)
                context_parts.append(f"- {tool_call.tool}: {self._summarize_result(result)}")

    context = "\n".join(context_parts)

    # Ask LLM to plan next step
    system_prompt = """
    You are planning the next action in a conversation.

    Based on what we've learned so far, decide:
    1. What tools to call next (if any)
    2. Or if we have enough information to respond to the user

    If previous tools failed or returned empty results, try alternatives:
    - Different dates
    - Different search criteria
    - Different approach entirely

    If we have good results, return empty tools list to signal we're done.
    """

    planning_result = await self.llm_client.plan(
        message=context,
        system_prompt=system_prompt
    )

    return planning_result

def _summarize_result(self, result):
    """Summarize result for context"""
    if isinstance(result, dict):
        if "error" in result:
            return f"❌ ERROR: {result['error']}"
        elif "available_rooms" in result:
            rooms = result.get("available_rooms", [])
            if not rooms:
                return "❌ No availability"
            return f"✓ Found {len(rooms)} rooms"
        elif "check_in" in result:
            return f"✓ Dates: {result['check_in']} to {result['check_out']}"
    return "✓ Success"
```

**Pros:** Full adaptability like Gemini CLI
**Cons:** More complex, more LLM calls

---

### Option C: Hybrid (RECOMMENDED)

**Combines your efficiency with Gemini's adaptability:**

```python
class Orchestrator:
    async def process_message(self, message, max_adaptation_turns=1):
        """Hybrid: Upfront planning + adaptive recovery"""

        # PHASE 1: Your strength - upfront planning
        initial_plan = await self.planner.plan(message)

        # PHASE 2: Execute with wave-based parallelism
        results = await self.runtime.execute(initial_plan.tools)

        # PHASE 3: Intelligent validation
        validation = await self.validator.analyze_results(
            user_message=message,
            plan=initial_plan,
            results=results
        )

        # PHASE 4: Adaptive recovery if needed
        if validation.needs_adaptation and max_adaptation_turns > 0:
            # Let LLM see results and decide next steps
            adaptation_plan = await self.planner.adapt(
                user_message=message,
                original_plan=initial_plan,
                original_results=results,
                validation_feedback=validation.feedback
            )

            if adaptation_plan.tools:
                # Execute additional tools
                additional_results = await self.runtime.execute(adaptation_plan.tools)

                # Merge results
                results.update(additional_results)

        # PHASE 5: Generate response
        response = await self.responder.generate(
            user_message=message,
            results=results
        )

        return response
```

**Validator Component:**

```python
class ResultValidator:
    """Analyzes tool results and decides if adaptation is needed"""

    async def analyze_results(
        self,
        user_message: str,
        plan: PlanningResult,
        results: Dict[str, Any]
    ) -> ValidationResult:
        """Check if results are good enough or need adaptation"""

        issues = []

        # Check for explicit errors
        for tool_id, result in results.items():
            if isinstance(result, dict) and "error" in result:
                issues.append({
                    'type': 'error',
                    'tool_id': tool_id,
                    'message': result['error']
                })

        # Check for empty availability
        availability_results = [
            (tid, r) for tid, r in results.items()
            if 'availability' in tid
        ]

        for tool_id, result in availability_results:
            if isinstance(result, dict):
                rooms = result.get('available_rooms', [])
                if not rooms:
                    issues.append({
                        'type': 'no_availability',
                        'tool_id': tool_id,
                        'message': 'No rooms available for requested dates'
                    })

        # Decide if adaptation is needed
        needs_adaptation = len(issues) > 0

        # Generate feedback for planner
        feedback = self._generate_feedback(user_message, issues)

        return ValidationResult(
            needs_adaptation=needs_adaptation,
            issues=issues,
            feedback=feedback
        )

    def _generate_feedback(self, user_message, issues):
        """Generate natural language feedback for planner"""
        if not issues:
            return None

        feedback_parts = ["The initial plan had these issues:"]

        for issue in issues:
            if issue['type'] == 'error':
                feedback_parts.append(f"- {issue['tool_id']} failed: {issue['message']}")
            elif issue['type'] == 'no_availability':
                feedback_parts.append(f"- No rooms available for the requested dates")

        feedback_parts.append("\nSuggestions:")
        feedback_parts.append("- Try nearby dates")
        feedback_parts.append("- Try shorter stay duration")
        feedback_parts.append("- Check different room types")

        return "\n".join(feedback_parts)
```

**Planner Adaptation Method:**

```python
# Add to ToolPlanner class

async def adapt(
    self,
    user_message: str,
    original_plan: PlanningResult,
    original_results: Dict[str, Any],
    validation_feedback: str
) -> PlanningResult:
    """Re-plan based on results and feedback"""

    context = f"""
## Original User Request
{user_message}

## What We Tried
{original_plan.action}

## What Happened
{self._format_results_summary(original_results)}

## Issues
{validation_feedback}

## Your Task
Based on what happened, plan alternative tools to try.
Be creative - try different dates, different approaches, etc.
If no reasonable alternatives exist, return empty tools list.
"""

    # Call planner with adaptation context
    adapted_plan = await self.plan(
        message=context,
        context=None  # Context is in the message itself
    )

    return adapted_plan

def _format_results_summary(self, results):
    """Format results for adaptation context"""
    summary = []
    for tool_id, result in results.items():
        if isinstance(result, dict):
            if "error" in result:
                summary.append(f"- {tool_id}: ❌ {result['error']}")
            elif "available_rooms" in result:
                count = len(result.get("available_rooms", []))
                summary.append(f"- {tool_id}: Found {count} rooms")
            else:
                summary.append(f"- {tool_id}: ✓ Success")
    return "\n".join(summary)
```

**Pros:**
- ✅ Most requests work with efficient upfront planning (like yours)
- ✅ Adapts when needed (like Gemini CLI)
- ✅ Doesn't always require multiple LLM calls
- ✅ Clear separation of concerns

**Cons:**
- Moderate complexity
- Need to build validator component

---

## Comparison of Options

| Aspect | Option A (Retry) | Option B (Iterative) | Option C (Hybrid) |
|--------|------------------|----------------------|-------------------|
| **Complexity** | Low | High | Medium |
| **LLM Calls** | 2 (plan + response) | 3-6 (multiple turns) | 2-3 (plan + adapt if needed) |
| **Cost** | Low | High | Medium |
| **Adaptability** | Limited (retries only) | Full | Full when needed |
| **Keeps Your Strengths** | ✅ Yes | ❌ Replaces them | ✅ Yes |
| **Success Rate** | 🟡 Medium | ✅ High | ✅ High |
| **Implementation Time** | 1-2 days | 3-4 days | 2-3 days |

---

## Recommended Implementation: Option C (Hybrid)

### Why Hybrid is Best for You

1. **Preserves your efficiency** - Most requests still use upfront planning
2. **Adds adaptability** - Recovers from failures like Gemini CLI
3. **Balanced cost** - Only adds extra LLM call when needed
4. **Clear architecture** - Validator is separate, easy to test
5. **Incremental rollout** - Can start with simple validation, enhance later

### Implementation Steps

**Week 1: Basic Validation**
```python
# Simple validator that checks for errors and empty results
# If found, trigger one adaptation turn
```

**Week 2: Smart Adaptation**
```python
# Enhance planner with adapt() method
# Add context about what failed and why
```

**Week 3: Advanced Heuristics**
```python
# Validator learns common patterns:
# - No availability → try nearby dates
# - Too expensive → suggest cheaper rooms
# - Too many nights → try shorter stay
```

---

## Example Flow with Hybrid

```
User: "Check availability for Hanukkah"

PHASE 1: Upfront Planning (your strength)
  Planner → [calendar("Hanukkah"), availability(dates=TBD)]

PHASE 2: Execute
  calendar → "8 nights: Dec 14-22"
  availability(8 nights) → [] (empty)

PHASE 3: Validate
  Validator: "No availability found, suggests trying shorter stay"

PHASE 4: Adapt
  Planner sees validation feedback:
    "Previous plan got 8 nights but no availability.
     Try 2-night weekend stay instead"

  Adapted plan → [availability(Dec 14-16, 2 nights)]

PHASE 5: Execute Adaptation
  availability(2 nights) → [Room A, Room B]

PHASE 6: Response
  "Hanukkah runs Dec 14-22. For the full 8 nights, we're fully booked,
   but I found availability for a weekend stay (Dec 14-16)..."

✅ Helpful response with smart adaptation
```

---

## Key Differences from Current System

| Current | With Feedback Loop |
|---------|-------------------|
| Planner is blind to results | Planner sees results and adapts |
| One-shot execution | Can iterate if needed |
| Fails on edge cases | Handles edge cases gracefully |
| Can't try alternatives | Automatically tries alternatives |
| "No availability" (unhelpful) | "No availability for X, but Y works!" (helpful) |

---

## Next Steps

1. **Decide on approach** - I recommend Option C (Hybrid)
2. **Build validator component** - Analyze results and decide if adaptation needed
3. **Add planner.adapt() method** - Re-plan based on feedback
4. **Update orchestrator** - Add validation + adaptation phases
5. **Test edge cases** - No availability, errors, etc.

Want me to start implementing the Hybrid approach?
