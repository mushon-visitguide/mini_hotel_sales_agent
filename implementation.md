Love it. Here’s a clean, production-ready v2 that rebuilds your agent end-to-end around four big ideas:

Price-by-construction (no “safety net”)

Claude-style TodoLoop for composite intents

Dynamic replanning (outcome-triggered)

Generic transform tools for JSON (rank/sort/filter/join)

I kept the design small, explicit, and testable.

Hotel Reservation Agent — v2 (TodoLoop + Provenance Pricing)
🎯 Goals

Answer composite requests in one turn (e.g., “suite next weekend, else closest dates, what’s the cancel policy?”).

Never hallucinate prices: only render Quote objects produced by PMS tools.

Be fast: parallel where safe; tiny steps; quick replans when outcomes aren’t ideal.

Stay readable: single orchestrator, small tools, typed I/O, thin NLG.

📁 Repository Layout
hotel_agent/
├── main.py
├── config.py
│
├── agent/
│   ├── orchestrator.py          # Brain: loops plan → run → todo → replan → nlg
│   ├── nlu.py                   # Rules first, LLM fallback hook
│   ├── planner.py               # Initial plan + micro-replanner hooks
│   ├── runtime.py               # Parallel waves, micro-waves, timeouts, retries
│   ├── todo.py                  # NEW: Goal, TodoItem, TodoLoop (Claude-style)
│   ├── nlg.py                   # Templating; gated price renderer
│   ├── policy.py                # Lightweight invariants (no freeform price)
│   └── state.py                 # ConversationState, BookingState
│
├── tools/
│   ├── registry.py              # Tool lookup + typed dispatch
│   ├── schemas.py               # Pydantic models (tool I/O, Quote, Money, etc.)
│   ├── pms_tools.py             # PMS wrappers (availability, policies, link)
│   ├── date_tools.py            # Fuzzy dates → concrete (Asia/Jerusalem)
│   ├── calendar_tools.py        # Flexible windows, closest-date search
│   └── transform_tools.py       # NEW: select/sort/filter/rank/join/derive
│
├── pms/
│   ├── ezgo_client.py
│   └── exceptions.py
│
├── models/
│   ├── intents.py               # Intents + composite intent support
│   ├── responses.py             # Response templates + copy blocks
│   └── types.py                 # Money, Quote, RateRef, PolicyRef, Party, Stay
│
├── storage/
│   ├── session_store.py
│   └── cache.py                 # Room types, policies (TTL)
│
├── utils/
│   ├── date_parser.py           # Weekend resolution, locale holidays
│   └── validators.py            # Input guards
│
└── tests/
    ├── test_e2e.py
    ├── test_planner.py
    ├── test_todoloop.py
    ├── test_transform_tools.py
    ├── test_nlg_pricing.py
    └── fixtures/

🧩 Core Concepts
Price-by-Construction (no “safety net”)

Create types that make incorrect pricing outputs impossible:

# models/types.py
class Money(BaseModel):
    amount: Decimal
    currency: Literal["USD","EUR","ILS", ...]  # from config

class Quote(BaseModel):
    quote_id: str
    total: Money                # final, tax-inclusive if PMS says so
    per_night: Optional[Money]  # convenience, computed
    refundable: bool
    cancel_policy_id: str
    inclusions: list[str]       # e.g., "Breakfast", "City tax included"
    rate_ref: str               # rate/room linkage
    fetched_at: datetime
    source_step: str            # provenance (e.g., "pms.get_availability")


Only PMS tools can produce Quote.

NLG never interpolates raw numbers. Prices are printed only via render_price(Quote):

Formats currency/locale.

Attaches short cancellation summary (fetched or cached).

Raises if quote is stale or missing policy.

TodoLoop (Claude-style progress)

Represent the user’s request as a small, living checklist.

# agent/todo.py
class Goal(BaseModel):
    id: str
    description: str
    done_when: Callable[[State, dict], bool]

class TodoItem(BaseModel):
    id: str
    text: str
    status: Literal["pending", "in_progress", "done"]
    needs: list[str] = []
    produces: list[str] = []  # e.g., "dates", "availability", "policy_summary"

class TodoLoop:
    def evaluate(self, goal: Goal, todos: list[TodoItem], state, last_results) -> PlanDelta:
        """
        - Mark completed items based on predicates / last_results
        - If outcomes undesirable (no rooms, over budget...), append follow-up steps
        - Return PlanDelta: new PlanSteps to run (micro-wave), updated todos
        """


Why: small steps, observable progress, quick course-correction—without new agents.

Dynamic Replanning (Outcome Triggers)

Planner emits a first plan. After each runtime “wave,” TodoLoop inspects outcomes and can append micro-steps:

availability == [] → enqueue:

calendar.closest_dates(check_in/out, room_filter)

pms.get_availability(...) for candidates

min(quote.total) > budget_max → enqueue:

calendar.flexible_windows(...) (wider/weekday)

transform.rank(by="quote.total.amount", top_k=3)

Missing policy details → enqueue pms.get_policy(policy_id) for top 2 rates

No graph surgery—just appends new steps and runs another micro-wave.

Generic Transform Tools (safe JSON “jq”)

Small, pure tools with typed inputs/outputs:

transform.select(fields)
transform.sort(keys=[("quote.total.amount","asc"),("refundable","desc")])
transform.filter(expr)             # DSL or JMESPath/JSONata backend
transform.rank(metric, top_k, tie_breakers)
transform.group_by(key, aggs)
transform.join(on, left_keys, right_keys)
transform.derive(fields={...})     # computed columns


All transform outputs are schema-validated; rank attaches explanations for NLG.

🧠 Control Flow
Orchestrator Loop (high level)
process_message(session, message):
  state ← load(session) or init
  parse ← NLU.parse(message, state)
  plan  ← Planner.build(parse, state)          # initial DAG
  goal,todos ← Planner.seed_goal_and_todos(parse, state)

  do:
    results_wave ← Runtime.execute_next_wave(plan, state)
    plan_delta, todos ← TodoLoop.evaluate(goal, todos, state, results_wave)
    plan ← plan + plan_delta                    # append new steps if any
  while plan.has_remaining_steps()

  response ← NLG.compose(parse.intent, state, results, todos, goal)
  Policy.validate_output_ast(response)          # light invariants (no raw price)
  save(session, state)
  return response

Runtime (waves + micro-waves)

Build waves by dependencies.

Run wave in parallel (asyncio.gather) with timeouts + retries.

After each wave, give TodoLoop a chance to extend plan with a micro-wave, then execute immediately.

Strict argument substitution from prior step outputs.

🏗️ Planner (Composite Intent Aware)

CHECK_AVAILABILITY (composite example)
Input: “Find me a suite for next weekend; if none, show closest dates; also what’s the cancellation policy?”

Initial Plan

dates.resolve_hint("next weekend", tz="Asia/Jerusalem") → check_in/out

pms.get_room_types(hotel_id) (parallel)

pms.get_availability(hotel_id, check_in/out, filters={"suite"}, party, rate_code) (needs 1)

Seed Goal & Todos

Goal: “Provide suite options for requested dates OR closest alternative, with cancellation policy.”

Todos:

Resolve dates → produces dates

Fetch suite availability → produces availability

If empty: find closest dates with suites → produces alt_dates

For top 2 rates: fetch policy → produces policy_summary

Synthesize answer with ranked options

Outcome Triggers (TodoLoop)

If 2) availability == [] → append steps:

calendar.closest_dates(...)

pms.get_availability(...) for alt dates

Else (rooms found): append

transform.rank(metric="quote.total.amount", top_k=2)

pms.get_policy(policy_id) for those 2

NLG then presents options with price + policy in one turn.

🔧 Tools (Interfaces)
PMS Tools (typed)

get_room_types(hotel_id) -> list[RoomType]

get_availability(hotel_id, check_in, check_out, party, room_filter, board_filter, rate_code) -> list[{room_type, rate, Quote}]

get_policy(cancel_policy_id) -> PolicySummary

generate_booking_link(hotel_id, check_in/out, party, room_type_code, rate_code, board_code) -> URL

Only PMS tools produce Quote. Transform tools never change Quote amounts—only select/sort/rank.

Dates & Calendar

resolve_hint(hint, timezone) -> {check_in, check_out}

find_next_weekend(today, weeks_ahead) -> dates

closest_dates(check_in/out, room_filter, window=±3d) -> list[date_range]

flexible_windows(start, span, rules) -> list[date_range]

Transform Tools (examples)
# tools/transform_tools.py
sort(input: list[dict], keys: list[tuple[str, Literal["asc","desc"]]]) -> list[dict]
rank(input: list[dict], metric: str, top_k:int, tie_breakers: list[str]) -> dict{items, rationale}
filter(input: list[dict], expr: str) -> list[dict]  # small DSL / JMESPath
select(input: list[dict], fields: list[str]) -> list[dict]
derive(input: list[dict], fields: dict[str, str]) -> list[dict]  # expressions
join(left, right, on:str, how="inner") -> list[dict]

🗣️ NLG (Gated Pricing + Progress UX)

Gated price renderer:

def render_price(q: Quote) -> str:
    assert isinstance(q, Quote)
    # format currency/locale; include “refundable” & short policy tag
    ...


Copy pattern (compact, decision-ready):

Heading: date range (explicit dates, locale)

Top 2 options (ranked): room → render_price(quote) → policy tag → inclusions

Alt dates (if needed): “Closest availability” list with 1-click “Try these dates”

Checklist footer (from TodoLoop): ✔ dates, ✔ availability, ✔ policy

🔒 Policy (now tiny)

Assert that any price token in the response AST originates from a Quote.

Assert policy summaries come from pms.get_policy cache or fresh fetch.

Assert currency consistency with config.default_currency.

No “pricing safety net”; correctness is enforced by types and rendering gates.

🧪 Testing & Observability
Tests

E2E happy paths (weekend suite, policy included).

No-rooms path → closest dates appended automatically.

Budget path → broader search + cheaper suggestions.

NLG: snapshot tests verifying no raw numbers; only render_price(Quote) used.

Transforms: property tests (stable sort, top-k correctness, join integrity).

Runtime: timeouts, retries, dependency waves, micro-wave append.

Observability

Structured events:

[plan] steps=3 synthesis_hint=present_best_two_options
[todo] status: resolve_dates=done, availability=done, policy=pending
[replan] trigger=no_availability, appended=[calendar.closest_dates, pms.get_availability]
[tool] pms.get_availability duration=420ms items=5


Correlate with session_id. Add per-step timing and cache hits.

⚙️ Performance Notes

Parallel first wave: resolve_dates + get_room_types.

Speculative prefetch: if user mentions “policy”/“refundable”, prefetch policy for top 2 rates after availability returns.

Caching: room types (hours), policies (hours, keyed by cancel_policy_id), rate/room descriptions (day).

🧭 Edge Cases & Behaviors

Timezone: default Asia/Jerusalem. “Next weekend” resolves to Fri–Sat and Sat–Sun variants—ask which, or try both.

Multiple rooms / parties: Party supports adults, children_ages; derive babies (<2y) vs children (2–17y).

Currency: keep PMS currency; render local currency if configured with a clear note (“charged in ILS, shown in USD for convenience”).

Taxes/fees: Quote flags inclusions; NLG shows “Total incl. city tax” if PMS marks inclusive.

🗺️ Roadmap (later, not required)

LLM fallback in NLU when rule confidence < 0.7.

Learned re-ranking for options using click-throughs.

Optional DuckDB backend for transforms if datasets grow.

📌 Example: End-to-end (single turn)

User: “Find me a suite for next weekend, if not available show closest dates, also what’s the cancellation policy?”

Plan (initial): resolve dates; room types; availability (suite filter).

Wave 1: resolve_dates + get_room_types (parallel).

Wave 2: get_availability (uses resolved dates).

TodoLoop:

If rooms found → append transform.rank(top_k=2) + pms.get_policy for those 2 (micro-wave).

If none → append calendar.closest_dates + pms.get_availability (micro-wave), then same policy fetch.

NLG: Show top 2 options with render_price(Quote) + short policy tag, then alt dates if needed, plus visible checklist.

If you want, I can drop in skeletal code for TodoLoop, the transform tool interfaces, and the Quote-gated renderer next.