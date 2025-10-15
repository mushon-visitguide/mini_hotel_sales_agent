# ✅ COMPLETED: LLM-Based Tool Planning Refactoring (October 2025)

## What We Accomplished

Successfully refactored the hotel booking AI agent from static intent-based planning to **dynamic LLM-powered tool planning**. The system now uses OpenAI GPT-4o to decide which tools to call and how to execute them in parallel.

### Architecture Transformation

**Before (Static):**
```
User Message → IntentExtractor → Enum Intent → ActionPlanner loads YAML → Execute
```

**After (Dynamic):**
```
User Message → ToolPlanner (LLM) → Tools DAG → Runtime (parallel executor) → Results
```

### Key Changes

1. **Removed Static Planning**
   - ❌ Deleted `agent/core/planner.py` (ActionPlanner class)
   - ❌ Deleted `agent/llm/intent_extractor.py` (IntentExtractor)
   - ❌ Deleted `prompts/action_plans/*.yaml` (all static action templates)
   - ❌ Deleted `prompts/intent_extractor.yaml`

2. **Created Dynamic LLM Planning**
   - ✅ `agent/llm/tool_planner.py` - Unified LLM-based planner
   - ✅ `agent/core/runtime.py` - Wave-based DAG executor with parallel execution
   - ✅ `prompts/planner.yaml` - Dynamic tool planning prompt
   - ✅ `agent/llm/schemas.py` - Updated schemas (Intent → Action, added ToolCall & PlanningResult)

3. **Natural Language Actions**
   - Changed from: `intent: "CHECK_AVAILABILITY"` (enum)
   - Changed to: `action: "Search for available rooms for 2 adults next weekend"` (natural language)

4. **Tool DAG with Dependencies**
   - Tools have `id`, `tool`, `args`, and `needs` fields
   - `needs: []` = run in parallel
   - `needs: ["tool_id"]` = wait for dependency
   - Runtime organizes tools into waves using topological sorting

### Test Results

**12/12 tests PASSED** ✅ using **REAL APIs** (no mocks):
- OpenAI GPT-4o API for tool planning
- MiniHotel PMS API for availability checks
- Real FAQ data for room information

**Test Coverage:**
- `test_llm_intent.py` - 8 tests (tool planning, parallel execution, slot extraction)
- `test_orchestrator.py` - 4 tests (end-to-end with real PMS, multi-message conversations)

### How It Works

1. **User sends message**: "Looking for a room next weekend"

2. **LLM Planning** (ToolPlanner):
   ```
   Action: Search for available rooms
   Slots: {date_hint: "next weekend", adults: 2}
   Tools DAG:
     - get_room_info: faq.get_rooms_and_pricing (needs: [])
     - check_availability: pms.get_availability (needs: [])
   ```

3. **Runtime Execution**:
   ```
   Wave 1: [faq.get_rooms_and_pricing, pms.get_availability] ← parallel!
   ```

4. **Results returned with action + reasoning**

### Key Features

- ✅ **No Hardcoded Intents** - LLM decides dynamically based on tool registry
- ✅ **Parallel Execution** - Independent tools run simultaneously
- ✅ **DAG Support** - Tools can depend on other tools via `needs` field
- ✅ **Real APIs** - No mocks, everything is live
- ✅ **Natural Language Actions** - Human-readable action descriptions
- ✅ **OpenAI Structured Outputs** - 100% reliable JSON schema adherence

### Files to Run

```bash
# Interactive CLI
./run.sh

# Or manually:
source venv/bin/activate
source .env
export PYTHONPATH=$(pwd):$PYTHONPATH
python main.py

# Run tests
pytest agent/tests/ -v
```

### Dependencies Added

- `openai>=1.0.0` - OpenAI API for LLM planning
- `pydantic>=2.0.0` - Schema validation
- `pyyaml` - YAML prompt loading

---

# Original Planning Document

Skip to content
Chat history

You said:
ok now based on those fixes I need you to create the full plan for my developer which describes all parts, few code example (but only critical places) explain the goal the steps the componetn flow everything, think hard on this full descriptive plan


lt["children_ages"] = [int(a) for a in ages if 0 <= int(a) <= 17]
        
        return result
    
    def _extract_bed_preference(self, msg: str) -> str:
        """Extract bed preference"""
        for keyword, value in self.BED_KEYWORDS.items():
            if keyword in msg:
                return value
        return None
    
    def _extract_budget(self, msg: str) -> float:
        """Extract budget constraint like 'under $150'"""
        match = re.search(r'under\s*\$?(\d+)', msg)
        if match:
            return float(match.group(1))
        
        match = re.search(r'\$(\d+)\s*(?:max|maximum|budget)', msg)
        if match:
            return float(match.group(1))
        
        return None


# Why this works:
# 1. Fast (< 1ms for rules)
# 2. Deterministic (same input = same output)
# 3. Testable (each rule is a unit test)
# 4. Extensible (add LLM fallback for low confidence)
--- ### 4. agent/planner.py - Build Execution Plan **Responsibility**: Decide which tools to call and in what order (the strategy)
python
# agent/planner.py
"""
Planner - Decides what tools to call and when
Creates a DAG (Directed Acyclic Graph) of tool calls
Identifies which can run in parallel
"""
from typing import List, Dict, Any
from models.intents import Intent
from agent.state import ConversationState
from dataclasses import dataclass

@dataclass
class PlanStep:
    """A single step in the execution plan"""
    id: str                    # Unique identifier
    tool: str                  # Tool name from registry
    args: Dict[str, Any]       # Arguments to pass
    needs: List[str] = None    # Step IDs this depends on
    parallel_safe: bool = True # Can run in parallel with siblings?
    
    def __post_init__(self):
        if self.needs is None:
            self.needs = []

@dataclass
class Plan:
    """Complete execution plan"""
    steps: List[PlanStep]
    synthesis_hint: str = None  # Hint for NLG about what to emphasize


class Planner:
    """
    Builds execution plans based on intent and current state
    
    Philosophy: Like Claude Code deciding which tools to use
    Plans are explicit, inspectable, and testable
    """
    
    def build_plan(
        self,
        parse_result: Dict,
        state: ConversationState
    ) -> Plan:
        """
        Main planning method - routes to intent-specific planners
        """
        intent = parse_result["intent"]
        slots = parse_result["slots"]
        
        # Route to appropriate planner
        if intent == Intent.CHECK_AVAILABILITY:
            return self._plan_availability_check(slots, state)
        
        elif intent == Intent.CONFIRM_SELECTION:
            return self._plan_selection(slots, state)
        
        elif intent == Intent.GENERATE_LINK:
            return self._plan_link_generation(slots, state)
        
        elif intent == Intent.ASK_AMENITIES:
            return self._plan_amenity_query(slots, state)
        
        elif intent == Intent.MODIFY_STAY:
            return self._plan_modification(slots, state)
        
        elif intent == Intent.COMPARE_OPTIONS:
            return self._plan_comparison(slots, state)
        
        else:
            # No tool calls needed (greeting, chat, etc.)
            return Plan(steps=[], synthesis_hint="conversational")
    
    def _plan_availability_check(
        self,
        slots: Dict,
        state: ConversationState
    ) -> Plan:
        """
        Plan for CHECK_AVAILABILITY intent
        
        Logic:
            1. Need dates? → resolve them first (if fuzzy)
            2. Have dates? → get availability + room types in PARALLEL
        """
        steps = []
        hotel_id = state.booking.hotel_id
        
        # STEP 1: Resolve dates if needed
        has_dates = state.booking.stay.check_in and state.booking.stay.check_out
        date_hint = slots.get("date_hint")
        
        if not has_dates and date_hint:
            # Need to resolve fuzzy date first
            steps.append(PlanStep(
                id="resolve_dates",
                tool="dates.resolve_hint",
                args={"hint": date_hint, "timezone": "Asia/Jerusalem"},
                parallel_safe=False  # Must complete before availability check
            ))
            date_dependency = ["resolve_dates"]
        elif not has_dates:
            # Missing dates and no hint - can't search yet
            # Return empty plan (NLG will ask for dates)
            return Plan(steps=[], synthesis_hint="ask_for_dates")
        else:
            # Already have dates
            date_dependency = []
        
        # STEP 2: Get room types (always, can cache)
        steps.append(PlanStep(
            id="get_room_types",
            tool="pms.get_room_types",
            args={"hotel_id": hotel_id},
            needs=[],  # Independent
            parallel_safe=True
        ))
        
        # STEP 3: Check availability (if we have or will have dates)
        if has_dates or date_hint:
            # Prepare party info
            adults = slots.get("adults", state.booking.party.adults)
            children_ages = slots.get("children_ages", state.booking.party.children_ages)
            
            # Calculate babies (< 2 years) vs children (2-17)
            babies = sum(1 for age in children_ages if age < 2)
            children = sum(1 for age in children_ages if 2 <= age <= 17)
            
            # Room type filter (if preference stated)
            room_filter = "*ALL*"
            if slots.get("bed_pref"):
                room_filter = slots["bed_pref"].upper()
            elif state.booking.bed_pref:
                room_filter = state.booking.bed_pref.upper()
            
            steps.append(PlanStep(
                id="check_availability",
                tool="pms.get_availability",
                args={
                    "hotel_id": hotel_id,
                    # Note: dates might come from resolve_dates step
                    "check_in": state.booking.stay.check_in if has_dates else None,
                    "check_out": state.booking.stay.check_out if has_dates else None,
                    "adults": adults,
                    "children": children,
                    "babies": babies,
                    "room_type_filter": room_filter,
                    "board_filter": "*ALL*",
                    "rate_code": "USD"
                },
                needs=date_dependency,  # Depends on date resolution
                parallel_safe=True  # Can run parallel with get_room_types
            ))
        
        return Plan(
            steps=steps,
            synthesis_hint="present_best_two_options"
        )
    
    def _plan_selection(
        self,
        slots: Dict,
        state: ConversationState
    ) -> Plan:
        """
        Guest confirmed a room - no tools needed, just update state
        """
        # No tools needed - NLG will ask for contact info
        return Plan(
            steps=[],
            synthesis_hint="collect_guest_info"
        )
    
    def _plan_link_generation(
        self,
        slots: Dict,
        state: ConversationState
    ) -> Plan:
        """
        Generate booking link - single tool call
        """
        booking = state.booking
        
        # Validate we have everything
        if not (booking.selected_room_type and booking.name and booking.phone):
            return Plan(steps=[], synthesis_hint="missing_info_for_link")
        
        steps = [
            PlanStep(
                id="generate_link",
                tool="pms.generate_booking_link",
                args={
                    "hotel_id": booking.hotel_id,
                    "check_in": booking.stay.check_in,
                    "check_out": booking.stay.check_out,
                    "adults": booking.party.adults,
                    "children": len([a for a in booking.party.children_ages if 2 <= a <= 17]),
                    "babies": len([a for a in booking.party.children_ages if a < 2]),
                    "room_type_code": booking.selected_room_type,
                    "rate_code": booking.selected_rate_code or "USD",
                    "board_code": booking.selected_board_code or "BB"
                },
                needs=[],
                parallel_safe=True
            )
        ]
        
        return Plan(
            steps=steps,
            synthesis_hint="send_link_with_summary"
        )
    
    def _plan_amenity_query(
        self,
        slots: Dict,
        state: ConversationState
    ) -> Plan:
        """
        Guest asking about amenities - might need room types
        """
        steps = []
        
        # If we don't have room types cached, fetch them
        if not state.booking.room_types_cache:
            steps.append(PlanStep(
                id="get_room_types",
                tool="pms.get_room_types",
                args={"hotel_id": state.booking.hotel_id},
                needs=[],
                parallel_safe=True
            ))
        
        return Plan(
            steps=steps,
            synthesis_hint="answer_amenity_question"
        )
    
    def _plan_modification(
        self,
        slots: Dict,
        state: ConversationState
    ) -> Plan:
        """
        Guest changing requirements - re-check availability
        Similar to initial availability check but marks it as a modification
        """
        # Essentially same as availability check
        plan = self._plan_availability_check(slots, state)
        plan.synthesis_hint = "show_updated_options"
        return plan
    
    def _plan_comparison(
        self,
        slots: Dict,
        state: ConversationState
    ) -> Plan:
        """
        Guest asking about differences - use cached results
        """
        # No tools needed - work with cached availability
        return Plan(
            steps=[],
            synthesis_hint="explain_differences"
        )


# Key insight: The Planner is pure strategy
# It doesn't execute anything, just decides what SHOULD be executed
# This makes it easy to test and reason about
--- ### 5. agent/runtime.py - Execute Tools in Parallel **Responsibility**: Execute the plan efficiently (parallel when safe)
python
# agent/runtime.py
"""
Runtime - Executes plans with parallel execution where safe
Handles timeouts, retries, validation
"""
import asyncio
from typing import Dict, Any, List
from tools.registry import ToolRegistry
from agent.planner import Plan, PlanStep
from datetime import datetime

class Runtime:
    """
    Executes execution plans
    
    Key features:
    - Parallel execution of independent steps
    - Respects dependencies (needs)
    - Timeout handling
    - Result validation
    - Error recovery
    """
    
    def __init__(
        self,
        registry: ToolRegistry,
        default_timeout: float = 10.0
    ):
        self.registry = registry
        self.default_timeout = default_timeout
    
    async def execute(self, plan: Plan) -> Dict[str, Any]:
        """
        Execute plan with parallel execution where possible
        
        Algorithm:
            1. Build dependency graph
            2. Execute steps in waves (parallel within wave)
            3. Each wave waits for previous wave to complete
            4. Propagate results forward (for dependent steps)
        
        Returns:
            Dict mapping step IDs to their results
        """
        if not plan.steps:
            return {}
        
        # Track results and completion
        results: Dict[str, Any] = {}
        completed: set = set()
        
        # Organize steps by dependency level (waves)
        waves = self._organize_into_waves(plan.steps)
        
        # Execute each wave
        for wave_num, wave_steps in enumerate(waves):
            print(f"[Runtime] Executing wave {wave_num + 1} with {len(wave_steps)} steps")
            
            # Execute all steps in this wave in parallel
            wave_results = await self._execute_wave(
                wave_steps,
                results  # Previous results available for substitution
            )
            
            # Merge results
            results.update(wave_results)
            completed.update(step.id for step in wave_steps)
        
        return results
    
    def _organize_into_waves(
        self,
        steps: List[PlanStep]
    ) -> List[List[PlanStep]]:
        """
        Organize steps into waves based on dependencies
        
        Wave 0: Steps with no dependencies
        Wave 1: Steps that depend only on Wave 0
        Wave 2: Steps that depend on Wave 0 or 1
        etc.
        
        Example:
            Steps: A, B(needs=[A]), C(needs=[A]), D(needs=[B, C])
            Waves: [[A], [B, C], [D]]
        """
        waves: List[List[PlanStep]] = []
        remaining = list(steps)
        completed_ids = set()
        
        while remaining:
            # Find steps that can execute now (all dependencies met)
            ready = [
                step for step in remaining
                if all(dep_id in completed_ids for dep_id in step.needs)
            ]
            
            if not ready:
                # Circular dependency or invalid plan
                raise ValueError(
                    f"Cannot resolve dependencies. "
                    f"Remaining: {[s.id for s in remaining]}"
                )
            
            waves.append(ready)
            completed_ids.update(step.id for step in ready)
            remaining = [s for s in remaining if s not in ready]
        
        return waves
    
    async def _execute_wave(
        self,
        steps: List[PlanStep],
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute all steps in a wave in parallel
        """
        # Create tasks for each step
        tasks = [
            self._execute_step(step, previous_results)
            for step in steps
        ]
        
        # Execute all in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Package results
        wave_results = {}
        for step, result in zip(steps, results):
            if isinstance(result, Exception):
                print(f"[Runtime] Step {step.id} failed: {result}")
                wave_results[step.id] = {"error": str(result)}
            else:
                wave_results[step.id] = result
        
        return wave_results
    
    async def _execute_step(
        self,
        step: PlanStep,
        previous_results: Dict[str, Any]
    ) -> Any:
        """
        Execute a single step with timeout
        
        Substitutes arguments from previous results if needed
        """
        # Substitute args from previous results
        args = self._substitute_args(step.args, previous_results)
        
        print(f"[Runtime] Executing {step.tool}({list(args.keys())})")
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                self.registry.call(step.tool, **args),
                timeout=self.default_timeout
            )
            
            print(f"[Runtime] {step.id} completed successfully")
            return result
            
        except asyncio.TimeoutError:
            print(f"[Runtime] {step.id} timed out")
            raise TimeoutError(f"Tool {step.tool} timed out")
        
        except Exception as e:
            print(f"[Runtime] {step.id} failed: {e}")
            raise
    
    def _substitute_args(
        self,
        args: Dict[str, Any],
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Substitute arguments from previous step results
        
        Example:
            args = {"check_in": None, "check_out": None}
            previous_results = {"resolve_dates": {"check_in": "2024-10-19", ...}}
            
            Returns: {"check_in": "2024-10-19", "check_out": "2024-10-21"}
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
        Find a key in nested results
        """
        for step_result in results.values():
            if isinstance(step_result, dict) and key in step_result:
                return step_result[key]
        return None


# Example execution:
# Plan:
#   Step A: resolve_dates (no dependencies)
#   Step B: get_room_types (no dependencies)
#   Step C: check_availability (needs A)
#
# Execution:
#   Wave 1: [A, B] execute in parallel
#   Wave 2: [C] executes (with dates from A)
--- ## 🎯 Key Design Principles ### 1. Separation of Concerns - **Orchestrator**: Coordinates - **NLU**: Understands - **Planner**: Decides - **Runtime**: Executes - **NLG**: Responds - **Policy**: Validates ### 2. Testability - Each component has clear inputs/outputs - No hidden state - Pure functions where possible - Easy to mock for tests ### 3. Parallel Execution - Independent tools run simultaneously - Respects dependencies automatically - Reduces latency significantly ### 4. Safety First - Never hallucinate prices - Always validate tool outputs - Timeout protection - Error recovery ### 5. Extensibility - Add new intents: extend NLU + Planner - Add new tools: register with schema - Add new channels: wrap orchestrator - No core changes needed --- ## 🔄 Complete Flow Example
User: "looking for a room next weekend"
     ↓
main.handle_message(session_id, message)
     ↓
Orchestrator.process_message()
     ├─> Load State (from session_id)
     ├─> NLU.parse()
     │    └─> Returns: {intent: CHECK_AVAILABILITY, 
     │                   slots: {date_hint: "next weekend"}}
     ├─> Planner.build_plan()
     │    └─> Returns: Plan with 3 steps:
     │         • resolve_dates (no deps)
     │         • get_room_types (no deps)
     │         • check_availability (needs resolve_dates)
     ├─> Runtime.execute()
     │    ├─> Wave 1: [resolve_dates, get_room_types] in parallel
     │    └─> Wave 2: [check_availability] with dates from Wave 1
     ├─> Update State with results
     ├─> NLG.compose()
     │    └─> "Next weekend would be Oct 19-20. Fri-Sat or Sat-Sun?"
     ├─> Policy.validate()
     ├─> Save State
     └─> Return response
--- ## 📊 Module Responsibilities Summary | Module | Responsibility | Key Methods | |--------|---------------|-------------| | main.py | Entry point | handle_message() | | orchestrator.py | Coordinate flow | process_message() | | nlu.py | Extract intent | parse(), _classify_intent() | | planner.py | Build execution plan | build_plan(), _plan_*() | | runtime.py | Execute in parallel | execute(), _execute_wave() | | nlg.py | Generate responses | compose() | | policy.py | Safety validation | validate_response() | | state.py | State definitions | ConversationState class | | pms_tools.py | PMS integration | Tool functions | | date_tools.py | Date resolution | resolve_hint() | | registry.py | Tool registry | register(), call() | --- ## Next Steps 1. Implement remaining modules (NLG, Policy, Date Tools) 2. Add tool schemas 3. Implement state persistence 4. Write conversation tests 5. Add LLM fallback to NLU (for low confidence) 6. Deploy! This design is production-ready, testable, and maintainable. please inspect my design , I need it to be liek the best ai agent exisrts read from the ineternt forums and articles specificaly dive into claude code and find out why it is so good and based on it suggest ideas or things to imrpove but still it should be simple deisng easyt to understand and read
ChatGPT said:

Thought for 36s
awesome — I took your current design (NLU → Planner → Runtime → NLG/Policy) and turned it into a full, developer-ready plan. I also dug into how Claude Code/Artifacts/Projects work and folded the best ideas in, while keeping the system simple and testable.

Goal (1 paragraph)
Ship a reliable hotel-booking agent that responds in seconds, never hallucinates prices, and executes tool calls in the right order (and in parallel when safe). The agent should be transparent (inspectable plans), resilient (timeouts/retries), and easy to extend (add intents/tools with zero core changes).

What Claude Code gets right (and what we’ll borrow)
Agentic loop with inspectable plans. Claude Code emphasizes explicit planning and iterative execution inside developer workflows; Anthropic’s “best practices for agentic coding” stresses decomposing tasks, parallelizing independent calls, and keeping the loop inspectable for humans. We mirror this with a DAG planner + wave executor. 
Anthropic

Projects = long-lived context. Persistent workspaces with large context windows (Projects) make the model consistent across long tasks; we adopt a lightweight “Project Store” (conversation-scoped memory of facts, caches, traces). 
Anthropic

Artifacts = separate, editable output pane. Claude’s “Artifacts” isolates substantial outputs (docs, code) from chat. We’ll produce structured “Artifacts” for quotes, room tables, and links so users can act on them without scrolling chat. 
Claude Help Center
+1

Enterprise-grade integration & scale. Big context, GitHub/codebase integration, and rollout to teams informs our emphasis on strong observability, admin controls, and reproducible evals as we grow. 
Constellation Research Inc.
+1

Reasoning modes. Anthropic’s newer “extended thinking” modes/variants suggest using a critic pass only when confidence is low, not by default (keeps latency snappy). 
Reuters

System at a glance
Modules (clean separation):

NLU – fast rules first; LLM fallback; confidence scoring and slot merge

Planner – builds a DAG of tool steps; identifies parallel waves; adds synthesis_hint

Runtime – executes waves in parallel; timeouts, retries, idempotency; injects outputs back into state

NLG – deterministic templates + artifact builders; style driven by synthesis_hint

Policy – price/PII validation and guardrails; error texts

Project Store (new) – cache, traces, and facts (dates resolved, room type cache, prior quotes); like Claude “Projects” but tiny and local to a session 
Anthropic

Indexing (new, tiny) – date/time normalizer, currency normalizer, and a mini term index for room/amenity synonyms to boost recall (inspired by codebase indexing discussions). 
Reddit

Observability (new) – per-step timings, tool args/returns, plan rendering, error taxonomy

Component flow (happy path)
User → NLU.parse() → intent + slots (+ confidences)
→ Planner.build_plan() → Plan(steps=[…], synthesis_hint=…)
→ Runtime.execute(plan) → waves in parallel; results dict
→ State update (Project Store caches room_types/availability)
→ NLG.compose() (templates + Artifacts)
→ Policy.validate() → final response

Improvements over your current design (inspired by Claude Code)
Confidence-aware NLU merge. Keep your fast regex rules, but always attach a confidence and merge with an LLM fallback only when needed.

Playbooks (micro-plans). For frequent intents (availability, modification, link gen), store parameterized “plan skeletons” that the Planner fills; this makes behavior consistent and debuggable (akin to repeatable agent “macros”). 
Anthropic
+1

Parallel first mindset. You already have wave execution; add a concurrency cap and short-circuit behavior when any mandatory step fails. (Claude’s guidance: parallel independent subtasks.) 
Anthropic
+1

Artifacts for outputs. Render availability tables, comparison diffs, and the booking link as structured artifacts (copyable, shareable), mirroring Claude’s UX. 
Claude Help Center

Project Store. Persist room_types, last quotes, user bed/board prefs, timezone (“Asia/Jerusalem”), and date resolutions; prevents re-asking and reduces latency. 
Anthropic

Critic-only-when-needed. If NLU confidence low or plan fails, run a cheap critic pass; otherwise skip for speed (similar to “extended thinking when helpful”). 
Reuters

Deterministic currency/date normalization. Don’t leave this to the LLM; use a tiny normalizer so “under $150” or “₪500 max” map to a numeric budget with ISO currency.

Tool schema validation. Validate args with JSON Schema/Pydantic before calls; log redacted args/returns for reproducibility.

Cost controls. Cache tool responses by (hotel_id, dates, party, filters); auto-dedupe simultaneous identical steps within a wave.

Observability and evals. Emit traces with: plan graph, step timings, cache hits, and NLG path; run nightly conversation replays.

Critical code examples (minimal, surgical)
1) NLU confidence merge (rules → fallback)
# nlu.py
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class ParseResult:
    intent: str
    slots: Dict[str, Any]
    confidence: float
    needs_fallback: bool = False

class NLU:
    def parse(self, msg: str) -> ParseResult:
        rule = self._rules(msg)               # your existing fast path
        if rule.confidence >= 0.8:
            return rule
        # call LLM only for unresolved or low-conf slots
        llm = self._fallback_llm(msg, unresolved=rule.unresolved_slots)
        merged = self._merge(rule, llm)
        merged.needs_fallback = True
        return merged
2) Budget & currency normalizer (fixes to your _extract_budget)
# nlu_normalizers.py
import re
from decimal import Decimal

CURRENCIES = {"$":"USD","₪":"ILS","usd":"USD","ils":"ILS","eur":"EUR"}
PAT = re.compile(r'(under|<=|less than|up to)?\s*(₪|\$|€)?\s*(\d{1,6})\s*(ils|usd|eur)?', re.I)

def parse_budget(msg: str) -> Optional[dict]:
    m = PAT.search(msg)
    if not m: return None
    op, sym, num, code = m.groups()
    ccy = CURRENCIES.get((sym or '').lower(), CURRENCIES.get((code or '').lower(), "USD"))
    return {"amount": Decimal(num), "currency": ccy, "operator": "<=" if op else None}
3) Planner playbooks (keeps it simple & testable)
# agent/playbooks.py
AVAILABILITY = [
  {"id":"maybe_resolve_dates", "tool":"dates.resolve_hint", "needs":[]},
  {"id":"get_room_types",      "tool":"pms.get_room_types", "needs":[]},
  {"id":"check_avail",         "tool":"pms.get_availability","needs":["maybe_resolve_dates"]}
]
# agent/planner.py (inside _plan_availability_check)
from agent.playbooks import AVAILABILITY
steps = instantiate_playbook(AVAILABILITY, slots, state)
return Plan(steps=steps, synthesis_hint="present_best_two_options")
4) Runtime: concurrency cap, retries, and idempotency
# agent/runtime.py
import asyncio, random
from tenacity import retry, wait_exponential, stop_after_attempt

class Runtime:
    def __init__(self, registry, default_timeout=10.0, max_concurrency=6):
        self.registry = registry
        self.default_timeout = default_timeout
        self.sema = asyncio.Semaphore(max_concurrency)

    @retry(wait=wait_exponential(min=0.2, max=2), stop=stop_after_attempt(2))
    async def _execute_step(self, step, prev):
        args = self._substitute_args(step.args, prev)
        async with self.sema:
            return await asyncio.wait_for(self.registry.call(step.tool, **args), timeout=self.default_timeout)
5) Tool schema validation + redaction
# tools/registry.py
from pydantic import BaseModel, ValidationError

class ToolSpec(BaseModel):
    name: str
    schema: BaseModel  # pydantic model type
    fn: callable
    redact: set = set()  # keys to hide in logs

def safe_call(spec: ToolSpec, **kwargs):
    try:
        data = spec.schema(**kwargs)
    except ValidationError as e:
        raise ValueError(f"Bad args for {spec.name}: {e}")
    result = spec.fn(**data.dict())
    log(spec.name, {k: ("***" if k in spec.redact else v) for k,v in data.dict().items()})
    return result
6) NLG artifacts (Claude-style, but simple)
# nlg.py
def compose(hint, state, results):
    if hint == "present_best_two_options":
        return Artifact.table(rows=_top_two(results["check_availability"]))
    if hint == "send_link_with_summary":
        return Artifact.booking_link(url=results["generate_link"]["url"], meta=state.booking.summary())
    return Text.reply(_fallback_message(hint))
Data contracts (simple & strict)
dates.resolve_hint → {check_in: "YYYY-MM-DD", check_out: "YYYY-MM-DD", tz: "Asia/Jerusalem"}

pms.get_room_types → {room_types: [{code, name, beds, board_options, amenities:[…]}]}

pms.get_availability → {options: [{room_type_code, board_code, rate_code, price_total, currency, cancellable:bool, quota:int}]}

pms.generate_booking_link → {url, expires_at}

Each response is validated (Pydantic), stored in Project Store cache, and annotated with observability.trace_id.

Edge cases & rules (baked in)
Timezone: Always resolve fuzzy dates in "Asia/Jerusalem".

Babies vs children: <2 = babies; 2–17 = children (you already compute this).

Missing dates: Planner returns synthesis_hint="ask_for_dates" → NLG asks a crisp, two-option question (Fri–Sat vs Sat–Sun) rather than open-ended.

Price safety: Never synthesize prices; only show validated tool outputs; mark stale cache over 10 minutes old.

Observability (what we log)
Plan graph (JSON)

Wave timings, per-tool duration, retries, timeouts

Cache hits/misses, input hashes

NLG path (which hint/template, artifact kind)

Errors with taxonomy (TOOL_TIMEOUT, BAD_ARGS, UPSTREAM_4XX/5XX)

Evaluation & QA (fast to set up)
Conversation replays: 20 golden scripts (availability, modify stay, budget filters, link gen), assert on structured outputs (no string matching).

Fault injection: Randomly fail a tool call; expect retry or graceful apology.

Latency budget: p95 end-to-end < 2.5s for availability with cached room types; < 4s cold start.

A/B critic pass: Only invoke critic on confidence < 0.8 or plan failure; measure latency vs precision. 
Reuters

Implementation steps (1–3 weeks each, parallel where safe)
Week 1–2 – NLU confidence + normalizers

Implement budget/currency & date normalizers; add confidence merge (rules + fallback).

Week 1–2 – Tool schemas & registry hardening

Pydantic validation, redaction, idempotency keys.

Week 2–3 – Planner playbooks & hints

Encode 5 micro-plans; add synthesis_hint catalog.

Week 2–4 – Runtime robustness

Concurrency cap, retries, better error surfaces; keep your wave code.

Week 3–4 – Project Store & caching

Cache room types/availability; simple TTL + input hash.

Week 4 – NLG Artifacts

Table artifact, comparison artifact, booking-link artifact.

Week 4–5 – Observability + eval harness

JSON traces, golden tests, nightly replay.

Developer checklist (acceptance criteria)
 Unit tests per tool schema; planner topological order tested

 Confidence-aware NLU returns same intent on same input deterministically

 Parallel waves run; concurrency ≤ cap; retries ≤ 2

 No price text appears unless present in PMS output

 Artifacts render for options and link

 Cold start < 4s p95; warm < 2.5s p95

 Traces present for every response with plan graph

Notes on sources & rationale
Anthropic’s engineering guidance on agentic coding underpins our plan-and-execute loop, encouraging parallelization and keeping plans inspectable. 
Anthropic

Projects inform our session-scoped Project Store for long-running tasks and stable context. 
Anthropic

Artifacts inspire our structured result panels, separating “work product” from chat to reduce confusion. 
Claude Help Center
+1

Industry guidance on DAG-style agents and parallel execution supports our wave executor and playbooks. 
LangChain Blog
+1

Recent reporting on Claude’s reasoning modes motivates conditional critic passes rather than always-on chains of thought. 
Reuters

If you want, I can turn this into a repo scaffold (folders, stub classes, tests) and a short “runbook” for the team.

You said:
how the folder tree stucutre will will look like (think hard) what is the main componetn , what componet will talk to who? also where prompts will be wrtttenr as we need to control the behavior of the agent way of talking also we dont want to use regext but extract the parmeters via llm please provide more details
ChatGPT said:

Thought for 28s
love it — here’s a tight, developer-ready folder layout + “who talks to who”, plus a switch from regex to LLM-only parameter extraction with strict, typed JSON. I kept it simple, testable, and easy to grow.

Folder tree (opinionated, production-ready)
repo/
├─ apps/
│  ├─ api/                       # FastAPI/Express entrypoint (HTTP)
│  │  ├─ main.py
│  │  └─ routers/
│  │     └─ chat.py              # POST /chat -> Orchestrator.process()
│  └─ worker/                    # Optional: background jobs (warm caches, evals)
│
├─ agent/
│  ├─ core/
│  │  ├─ orchestrator.py         # MAIN component: coordinates the whole loop
│  │  ├─ planner.py              # Builds a DAG plan (waves, deps)
│  │  ├─ runtime.py              # Executes plan in parallel; retries/timeouts
│  │  ├─ policy.py               # Output guardrails (price/PII/claims)
│  │  ├─ state.py                # Conversation & Booking state models
│  │  ├─ memory.py               # “Project Store”: caches, user prefs, traces
│  │  └─ tracing.py              # OpenTelemetry/JSON logs + plan graph export
│  ├─ nlu/
│  │  ├─ extractor_llm.py        # LLM-based slot/intention extractor (no regex)
│  │  ├─ schema.py               # Pydantic models & JSON Schemas for NLU outputs
│  │  ├─ intents.py              # Enum + catalog of intents
│  │  └─ slot_logic.py           # Post-processing (e.g., babies vs children)
│  ├─ nlg/
│  │  ├─ composer.py             # Turns results into responses
│  │  ├─ artifacts.py            # Tables/links/comparison “artifacts”
│  │  └─ templates/              # Minimal Jinja/format templates
│  │     ├─ availability_table.md.j2
│  │     └─ booking_link.md.j2
│  ├─ playbooks/
│  │  ├─ availability.yaml       # Reusable micro-plan skeletons
│  │  ├─ modify.yaml
│  │  └─ link_generation.yaml
│  ├─ tools/
│  │  ├─ registry.py             # Tool registration, schema validation, redaction
│  │  ├─ date_tools.py           # Deterministic date math (no regex)
│  │  ├─ pms/
│  │  │  ├─ get_room_types.py
│  │  │  ├─ get_availability.py
│  │  │  └─ generate_link.py
│  │  └─ adapters/               # External APIs, retry/backoff, idempotency
│  └─ data_contracts/            # Pydantic models for tool I/O
│     ├─ pms_models.py
│     └─ shared.py
│
├─ prompts/                      # All prompts live here (versioned, testable)
│  ├─ system/                    # Base system personas & safety dials
│  │  └─ system.base.yaml
│  ├─ nlu/                       # Extractor prompts (JSON-mode + examples)
│  │  └─ extractor.booking.v1.yaml
│  ├─ nlg/                       # Style kits & behavior knobs
│  │  ├─ style.default.yaml
│  │  └─ style.brief.yaml
│  ├─ tools/                     # Tool-use guidance (per intent)
│  │  └─ availability.plan.yaml
│  └─ fragments/                 # Reusable blocks (tone, disclaimers, locale)
│     ├─ tz_asia_jerusalem.yaml
│     └─ safety_price_claims.yaml
│
├─ configs/
│  ├─ dev.yaml                   # Concurrency, timeouts, model names
│  ├─ prod.yaml
│  └─ features.yaml              # Flags (critic pass on/off, cache TTLs)
│
├─ tests/
│  ├─ unit/
│  │  ├─ test_nlu_extractor.py
│  │  ├─ test_planner.py
│  │  ├─ test_runtime_parallel.py
│  │  └─ test_policy.py
│  ├─ e2e/
│  │  └─ conversations/          # Golden scripts with assertions on JSON artifacts
│  └─ prompts/
│     └─ test_extract_examples.yaml
│
├─ docs/
│  ├─ architecture.md
│  ├─ plan_examples.md           # Rendered micro-plan DAGs (PNG/mermaid)
│  └─ runbook.md                 # Oncall, tracing, evals
│
├─ infra/
│  ├─ docker/
│  │  ├─ Dockerfile.api
│  │  └─ Dockerfile.worker
│  └─ k8s/
│     └─ deployments.yaml
└─ Makefile
Who talks to who (clear boundaries)
[API /apps/api] ──calls──> [Orchestrator (agent/core/orchestrator.py)]
       │                         │
       │                         ├─calls──> [NLU Extractor (agent/nlu/extractor_llm.py)]
       │                         │               └─reads prompts/nlu/*.yaml
       │                         │
       │                         ├─calls──> [Planner] -> returns Plan (DAG)
       │                         │               └─reads playbooks/*.yaml
       │                         │
       │                         ├─calls──> [Runtime] -> executes Tools via Registry
       │                         │               └─calls tools/* and adapters/*
       │                         │
       │                         ├─calls──> [NLG Composer] -> Artifacts/Templates
       │                         │               └─reads prompts/nlg/* + templates/*
       │                         │
       │                         ├─calls──> [Policy] -> final validation
       │                         │
       │                         └─calls──> [Memory/Project Store] for cache/prefs
       │
[outbound response] <──────────  orchestrator returns text + artifacts
Main component: Orchestrator. It is the single entry point and owns the loop:

call NLU → 2) Planner → 3) Runtime → 4) NLG → 5) Policy → 6) update Memory → return.

Tools are only called by Runtime through tools.registry (nowhere else).

Prompts: where & how we control agent behavior
All prompts are files under /prompts. We keep them short, modular, versioned, and testable.

prompts/system/system.base.yaml – persona, safety posture, response style defaults.

prompts/nlu/extractor.booking.v1.yaml – the LLM parameter extractor: JSON-schema, examples, locale hints.

prompts/tools/*.yaml – intent-specific guidance on which fields matter (helps Planner).

prompts/nlg/style.*.yaml – tone/voice dials (e.g., “brief, friendly, no emojis”, or “detailed”).

prompts/fragments/* – reusable snippets (timezone: Asia/Jerusalem; disclaimers for price claims, etc.).

We do not hardcode prompt text in Python. The Orchestrator loads prompt packs selected by env (dev/prod) + feature flags (e.g., “brief style”).

Minimal YAML example (NLU extractor):

# prompts/nlu/extractor.booking.v1.yaml
id: extractor.booking.v1
goal: "Extract intent and slots for hotel booking tasks. Output ONLY valid JSON."
constraints:
  json_schema:
    type: object
    properties:
      intent: {type: string, enum: ["CHECK_AVAILABILITY","MODIFY_STAY","ASK_AMENITIES","CONFIRM_SELECTION","GENERATE_LINK","COMPARE_OPTIONS","SMALL_TALK"]}
      slots:
        type: object
        properties:
          date_hint: {type: string, nullable: true}
          check_in: {type: string, pattern: "^[0-9]{4}-[0-9]{2}-[0-9]{2}$", nullable: true}
          check_out: {type: string, pattern: "^[0-9]{4}-[0-9]{2}-[0-9]{2}$", nullable: true}
          adults: {type: integer, minimum: 1, default: 2}
          children_ages: {type: array, items: {type: integer, minimum: 0, maximum: 17}, default: []}
          bed_pref: {type: string, nullable: true}
          budget: 
            type: object
            properties:
              amount: {type: number}
              currency: {type: string, enum: ["USD","EUR","ILS"], default: "USD"}
              operator: {type: string, enum: ["<=","~"], nullable: true}
            required: []
          compare_criteria: {type: array, items: {type: string}, default: []}
    required: ["intent","slots"]
locale_hints:
  timezone: "Asia/Jerusalem"
  date_formats: ["YYYY-MM-DD", "next weekend", "this Friday"]
style: "Be concise. No chit-chat. JSON only."
examples:
  - user: "We’re 2 adults + 1 kid(5), under ₪600 for next weekend."
    output: |
      {"intent":"CHECK_AVAILABILITY","slots":{"date_hint":"next weekend","adults":2,"children_ages":[5],"budget":{"amount":600,"currency":"ILS","operator":"<="}}}
Note: even the pattern guards in the schema are used by the validator in Python, not by regex scanning of the user text. The LLM generates the JSON; Pydantic/JSON Schema enforces shape.

LLM-only parameter extraction (no regex)
We only ask the LLM to emit a strict JSON object that matches our schema (intent + slots).

We validate with Pydantic; if validation fails, we ask the LLM once more with the error (chain-of-critique style), or fall back to a disambiguation prompt to the user.

Post-processing is deterministic (e.g., separating babies <2 vs children 2–17).

Budgets, currencies, bed preferences, ages, and fuzzy dates are all requested as structured fields in the JSON; no pattern matching on the raw text.

Critical code: LLM extractor wrapper

# agent/nlu/extractor_llm.py
from typing import Dict, Any
from pydantic import BaseModel, Field, ValidationError
import json

class Budget(BaseModel):
    amount: float | None = None
    currency: str | None = None  # "USD","EUR","ILS"
    operator: str | None = None  # "<=", "~"

class Slots(BaseModel):
    date_hint: str | None = None
    check_in: str | None = None
    check_out: str | None = None
    adults: int = 2
    children_ages: list[int] = Field(default_factory=list)
    bed_pref: str | None = None
    budget: Budget | None = None
    compare_criteria: list[str] = Field(default_factory=list)

class ParseResult(BaseModel):
    intent: str
    slots: Slots

class LLMExtractor:
    def __init__(self, llm_client, prompt_loader):
        self.llm = llm_client
        self.prompts = prompt_loader

    def parse(self, message: str) -> ParseResult:
        prompt = self.prompts.load("nlu/extractor.booking.v1.yaml")
        system_msg = self.prompts.system("system/system.base.yaml")
        messages = [
            {"role":"system", "content": system_msg},
            {"role":"user", "content": message},
            {"role":"system", "content": f"Follow these rules and output ONLY JSON.\nSchema:\n{json.dumps(prompt['constraints']['json_schema'])}"}
        ]
        raw = self.llm.complete(messages, response_format="json")  # or function-calling
        try:
            data = json.loads(raw)
            return ParseResult(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            # one retry with error surfaced to the LLM
            messages.append({"role":"system","content":f"Your JSON was invalid: {str(e)}. Output valid JSON only."})
            raw2 = self.llm.complete(messages, response_format="json")
            data2 = json.loads(raw2)
            return ParseResult(**data2)
Critical code: babies/children logic (no regex, just ints)

# agent/nlu/slot_logic.py
def split_children(children_ages: list[int]) -> dict:
    babies = sum(1 for a in children_ages if a < 2)
    children = sum(1 for a in children_ages if 2 <= a <= 17)
    return {"babies": babies, "children": children}
Planning & execution (kept simple)
Planner uses playbooks (/agent/playbooks/*.yaml) to keep plans consistent and readable.

Runtime executes waves in parallel; tools only called through the registry; retries & timeouts included.

Micro-plan (availability.yaml)

id: availability
steps:
  - id: maybe_resolve_dates
    tool: dates.resolve_hint
    args: {hint: "${slots.date_hint}", timezone: "Asia/Jerusalem"}
    run_if: "${slots.check_in is None or slots.check_out is None and slots.date_hint is not None}"
  - id: get_room_types
    tool: pms.get_room_types
    args: {hotel_id: "${state.booking.hotel_id}"}
  - id: check_availability
    tool: pms.get_availability
    needs: ["maybe_resolve_dates"]
    args:
      hotel_id: "${state.booking.hotel_id}"
      check_in: "${state.booking.stay.check_in or steps.maybe_resolve_dates.check_in}"
      check_out: "${state.booking.stay.check_out or steps.maybe_resolve_dates.check_out}"
      adults: "${slots.adults or state.booking.party.adults}"
      children: "${calc.children}"
      babies: "${calc.babies}"
      room_type_filter: "${slots.bed_pref or state.booking.bed_pref or '*ALL*'}"
      board_filter: "*ALL*"
      rate_code: "USD"
synthesis_hint: "present_best_two_options"
Planner (instantiate playbook + computed fields)

# agent/core/planner.py (excerpt)
from agent.nlu.slot_logic import split_children
from agent.playbooks.loader import load_playbook, render_args

def plan_availability(slots, state):
    play = load_playbook("availability")
    calc = split_children(slots.children_ages)
    steps = render_args(play["steps"], slots=slots, state=state, calc=calc)
    return Plan(steps=steps, synthesis_hint=play["synthesis_hint"])
Runtime concurrency + retries (essentials only)

# agent/core/runtime.py (excerpt)
import asyncio
from tenacity import retry, wait_exponential, stop_after_attempt

class Runtime:
    def __init__(self, registry, timeout=10.0, concurrency=6):
        self.registry = registry
        self.timeout = timeout
        self.sema = asyncio.Semaphore(concurrency)

    async def execute(self, plan):
        waves = self._topological_waves(plan.steps)
        results = {}
        for wave in waves:
            tasks = [self._run_step(s, results) for s in wave]
            wave_out = await asyncio.gather(*tasks, return_exceptions=True)
            for s, r in zip(wave, wave_out):
                results[s.id] = r if not isinstance(r, Exception) else {"error": str(r)}
        return results

    @retry(wait=wait_exponential(min=0.2, max=2), stop=stop_after_attempt(2))
    async def _run_step(self, step, prev):
        args = self._fill_args(step.args, prev)
        async with self.sema:
            return await asyncio.wait_for(self.registry.call(step.tool, **args), timeout=self.timeout)
NLG: style control + artifacts
Style kits in prompts/nlg/ control tone (“brief”, “friendly”, etc.).

composer.py picks a style kit based on synthesis_hint and environment.

Outputs are artifacts (tables, links), not just paragraphs.

Style kit (prompts/nlg/style.default.yaml)

voice: "concise, helpful, no emojis"
bullets: true
price_language: "Never invent prices. Only display tool outputs."
ack_confidence: false
Composer (core idea)

# agent/nlg/composer.py (excerpt)
def compose(hint: str, state, results, style):
    if hint == "present_best_two_options":
        options = top_two(results.get("check_availability", {}).get("options", []))
        return Artifacts.table("Top matches", rows=options, style=style)
    if hint == "send_link_with_summary":
        link = results["generate_link"]["url"]
        return Artifacts.link("Complete your booking", link, meta=state.booking.summary())
    return Text("I’ve updated your options above.")
Why this stays simple
Single main component (Orchestrator) calling four subsystems in order.

LLM extractor replaces regex entirely, but with strict schemas + one retry for robustness.

Playbooks make plans readable and easy to review in code reviews.

Artifacts keep the chat clean and actionable.

Memory/Project Store is just a thin cache + prefs per session (no vector DB required).

Dev tips & defaults
Timezone: default to Asia/Jerusalem everywhere (date resolver & style fragment).

Currency: accept USD/EUR/ILS from the extractor; keep everything typed.

Confidence: if the extractor returns missing critical fields twice → Planner yields synthesis_hint="ask_for_dates" and NLG asks a crisp, multiple-choice follow-up (not open-ended).

Observability: log every plan graph + wave timings; never log raw PII (use registry redaction).

If you want, I can drop in the scaffolding files for orchestrator.py, extractor_llm.py, the playbook loader, and two prompt packs so your team can make dev and start running end-to-end tests immediately.




No file chosenNo file chosen
ChatGPT can make mistakes. Check important info.
