Awesome—let’s design this like a Claude-Code-style, agent-agnostic system: a first-layer “brain” that plans and routes, a tool/capability layer with typed APIs (your PMS abstraction + holiday/calendaring + utilities), and a safe execution layer. I’ll give you the modules, object model, key functions, data contracts, and end-to-end flows (including parallel calls and replanning when the guest changes their mind). Citations explain the design inspirations (MCP/tools, ReAct/Toolformer, sub-agents). 
arXiv
+4
Claude Docs
+4
Claude Docs
+4

High-Level Architecture (Claude-Code-inspired)

Layer 1 — Orchestrator (First-Layer Agent / “Brain”)

Interprets intent & slots, plans a set of tool calls (possibly in parallel), evaluates results, and synthesizes the reply.

Stateless model + stateful Conversation Store (so the brain can change its mind while keeping the guest’s goal).

Uses a typed Tool Registry (like MCP servers/capabilities) so the “brain” is agnostic to specific PMSes. 
Claude Docs
+1

Layer 2 — Tool/Capability Layer

Your existing PMSClient (via PMSClientFactory) + HolidayProvider, FlexibleDateFinder, CalendarView, RoomTypeCatalog, Rules/Policy (e.g., never hallucinate price).

All exposed with JSON-schema tool signatures so any LLM with function calling can use them (ReAct/Toolformer patterns). 
arXiv
+1

Layer 3 — Execution Runtime

Async dispatcher that executes planned tool calls (in parallel where independent), normalizes/validates responses, handles retries/timeouts/idempotency, and returns structured results to Layer 1.

Cross-cutting

Conversation State (structured booking context + diffing), Policy Guardrails (no price hallucination), Observability/Analytics, Caching (static vs dynamic), Channel Adapters (Web/WhatsApp/Voice).

Module Map
/src
  /agent
    orchestrator.py          # First-layer agent brain
    planner.py               # Plan builder (DAG of tool calls)
    intent_router.py         # Intent taxonomy & router
    nlu.py                   # Intent + slot extraction
    nlg.py                   # Templating + safe price substitution
    policy.py                # Guardrails (no price hallucination)
    tool_registry.py         # Typed tool descriptions (schemas)
    runtime.py               # Async executor (parallel calls, retries)
    state.py                 # ConversationState, diff/replan logic
  /capabilities
    holidays.py              # HolidayProvider (e.g., public holidays/events)
    calendar_view.py         # Availability calendar/“next free weekend”
    flexible_dates.py        # 2-week windows / alternatives search
    room_catalog.py          # Cached room types & attributes
    post_booking.py          # Booking link generation + hold workflows
  /pms
    base.py                  # (you already have)
    minihotel_client.py      # (initial concrete impl)
    factory.py               # (you already have)
  /channels
    web_adapter.py
    whatsapp_adapter.py
    voice_adapter.py
  /infra
    cache.py                 # (Redis) static caches + short-lived memoization
    store.py                 # (Postgres) conversations, traces, test fixtures
    telemetry.py             # logs/metrics/traces
    config.py
  /tests
    conversations_test.py    # pulls from chat_conversations.md
    e2e_agent_tests.py

Core Data Contracts
Conversation State (persisted)
@dataclass
class GuestParty:
    adults: int
    children: int = 0
    babies: int = 0
    children_ages: Optional[List[int]] = None

@dataclass
class StayConstraints:
    check_in: Optional[date] = None
    check_out: Optional[date] = None
    nights: Optional[int] = None
    flexible: bool = False           # “next weekend”, “2 weeks in June”, etc.
    area: Optional[str] = None       # for multi-hotel future
    date_hints: Optional[str] = None # “Christmas period”, “end of next month”

@dataclass
class RoomPreferences:
    room_type_codes: Optional[List[str]] = None
    connecting: Optional[bool] = None
    features: Optional[List[str]] = None  # ["Ocean View", "Balcony"]
    bed_config: Optional[str] = None

@dataclass
class PricingSnapshot:
    currency: Optional[str] = None
    total_price: Optional[float] = None   # from PMS ONLY
    board_code: Optional[str] = None
    rate_code: Optional[str] = None
    last_refreshed_at: Optional[datetime] = None

@dataclass
class BookingContext:
    hotel_id: str
    parties: List[GuestParty]
    rooms_count: Optional[int] = None
    stay: StayConstraints = field(default_factory=StayConstraints)
    prefs: RoomPreferences = field(default_factory=RoomPreferences)
    pricing: Optional[PricingSnapshot] = None
    selected_room_type_code: Optional[str] = None
    selected_option_ref: Optional[str] = None   # opaque option id from PMS
    policy_notes: List[str] = field(default_factory=list)  # cancel policy, etc.

@dataclass
class ConversationState:
    goal: str = "FIND_AVAILABILITY"   # or "SELECT_OPTION" / "BOOK"
    turn_id: str = ""
    history: List[Dict[str, Any]] = field(default_factory=list)
    booking: BookingContext = field(default_factory=BookingContext)
    last_tool_results: Dict[str, Any] = field(default_factory=dict)

Intent & Plan
class Intent(str, Enum):
    CHECK_AVAILABILITY = "check_availability"
    ASK_ROOM_DETAILS  = "ask_room_details"
    FIND_FLEXIBLE     = "find_flexible_dates"     # “next weekend”, “two weeks”
    FIND_HOLIDAY      = "find_holiday_dates"
    SHOW_CALENDAR     = "calendar_view"
    QUOTE_SUMMARY     = "quote_summary"
    GENERATE_LINK     = "generate_booking_link"
    UPDATE_REQUIREMENT= "update_requirement"      # changes mid-convo
    FAQ_POLICY        = "faq_policy"

@dataclass
class PlanStep:
    id: str
    tool: str                 # one of Tool Registry names
    args: Dict[str, Any]
    needs: List[str]          # step ids this depends on
    provides: List[str]       # keys written to plan context
    parallelizable: bool = True
    timeout_s: int = 5
    retries: int = 1

@dataclass
class Plan:
    steps: List[PlanStep]
    synthesis_hint: Optional[str] = None  # NLG guide

Tool Registry (typed functions)

Think MCP-style descriptors: human+machine readable, JSON-schema parameters, declared side-effects. (The brain is tool-agnostic; you can swap PMS or holidays providers later.) 
Claude Docs
+1

# tools/availability.json (schema-like pseudo)
{
  "name": "pms.get_availability",
  "description": "Real-time availability and prices for a hotel and guest party.",
  "params": {
    "type": "object",
    "properties": {
      "hotel_id": {"type": "string"},
      "check_in": {"type": "string", "format": "date"},
      "check_out": {"type": "string", "format": "date"},
      "adults": {"type": "integer", "minimum": 1},
      "children": {"type": "integer", "minimum": 0},
      "babies": {"type": "integer", "minimum": 0},
      "rate_code": {"type": "string"},
      "room_type_filter": {"type": "string", "default": "*ALL*"},
      "board_filter": {"type": "string", "default": "*ALL*"}
    },
    "required": ["hotel_id","check_in","check_out","adults"]
  },
  "returns": {"$ref": "#/definitions/AvailabilityResponse"},
  "policy": {"no_price_hallucination": true}
}

{
  "name": "pms.get_room_types",
  "description": "Static room types and attributes (cacheable).",
  "params": {"type":"object","properties":{"hotel_id":{"type":"string"}},"required":["hotel_id"]},
  "returns": {"type":"array","items":{"$ref":"#/definitions/RoomType"}}
}

{
  "name": "holidays.get_period",
  "description": "Resolve named holidays/events to concrete date ranges for a given locale.",
  "params": {"type":"object","properties":{"locale":{"type":"string"},"hint":{"type":"string"}},"required":["hint"]}
}

{
  "name": "calendar.find_next_free_weekend",
  "description": "Find the next weekend with at least one available room for the party.",
  "params": {"type":"object","properties":{"hotel_id":{"type":"string"},"party":{"type":"object"},"weeks_ahead":{"type":"integer","default":8}},"required":["hotel_id","party"]}
}

{
  "name": "pms.generate_booking_link",
  "description": "Compose a deep link to booking engine with prefilled params.",
  "params": {"type":"object","properties":{
    "hotel_id":{"type":"string"},
    "check_in":{"type":"string","format":"date"},
    "check_out":{"type":"string","format":"date"},
    "adults":{"type":"integer","minimum":1},
    "children":{"type":"integer","minimum":0},
    "babies":{"type":"integer","minimum":0},
    "room_type_code":{"type":"string"},
    "rate_code":{"type":"string"},
    "board_code":{"type":"string"}
  },"required":["hotel_id","check_in","check_out","adults"]}
}


These registry entries are implemented by thin adapters that call your PMSClientFactory (MiniHotel first), plus provider classes for holidays/calendar.

Orchestrator Flow (plan → execute in parallel → synthesize)
sequenceDiagram
  participant G as Guest
  participant C as Channel Adapter
  participant O as Orchestrator (Brain)
  participant N as NLU (Intent+Slots)
  participant P as Planner
  participant R as Runtime (Exec)
  participant T as Tools (PMS/Holidays/Calendar)
  participant S as State Store

  G->>C: "Thinking next weekend... 2 nights, king bed"
  C->>O: normalized message
  O->>N: classify intent + extract slots
  N-->>O: Intent=CHECK_AVAILABILITY, slots={next weekend, 2 nights, king}
  O->>S: load conversation state
  O->>P: build plan (need dates→calendar & availability & room types)
  P-->>O: Plan: step A (resolve 'next weekend'); steps B,C in parallel
  O->>R: execute(plan)
  R->>T: holidays/calendar.resolve_next_weekend()
  T-->>R: concrete dates (Oct 19–21)
  par Parallel
    R->>T: pms.get_availability(Oct 19–21, 2A)
    R->>T: pms.get_room_types()
  end
  T-->>R: availability + room types
  R-->>O: aggregated results
  O->>S: update state (selected options, prices from PMS)
  O-->>C: NLG response (with safe price insertion)
  C-->>G: "Premium King $255/night ... book?"


Parallelization is inspired by “plan-first, execute tools, then synthesize”—common in ReAct-style agent designs and Claude Code’s multi-tool workflows/sub-agents. 
arXiv
+1

Key Components (OO design & main methods)
1) NLU (intent & slots)
class NLU:
    def parse(self, text: str, state: ConversationState) -> Dict[str, Any]:
        """
        Returns: {
          "intent": Intent,
          "slots": { "dates_hint": "next weekend", "nights": 2, "bed": "king", ... },
          "confidence": float
        }
        """


Use a small classifier or LLM prompt.

Normalize dates (“next weekend”, “Christmas period”, “end of next month”), numbers, room type mentions.

Emit missing slots so Planner knows what to fetch vs. what to clarify.

2) Planner (builds a DAG of steps)
class Planner:
    def build(self, intent: Intent, slots: Dict[str, Any], state: ConversationState) -> Plan:
        # Examples:
        # - For CHECK_AVAILABILITY with fuzzy dates:
        #   A: resolve dates (holidays/calendar/flexible_dates)
        #   B: pms.get_availability (depends: A)
        #   C: pms.get_room_types (parallel)
        #   Synthesis hint: "Compare by min price & features"


Emits parallelizable steps where safe (e.g., room types can always be fetched in parallel & cached).

For flexible requests (“two weeks in June”, “next available weekend”), emits batch availability checks across candidate windows to reduce back-and-forth latency.

3) Runtime (async executor)
class Runtime:
    async def execute(self, plan: Plan, registry: ToolRegistry, ctx: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes steps honoring dependencies. Parallel where possible (asyncio.gather).
        Retries transient errors, enforces timeouts, returns dict of {provided_key: value}.
        """


Each step’s provides keys are merged into a shared plan context.

Validates tool outputs (schemas).

Never fabricates prices; if missing, returns an error that NLG will surface politely.

4) Tool Registry & Adapters
class ToolRegistry:
    def register(self, name: str, func: Callable, schema: Dict[str, Any]): ...
    async def call(self, name: str, **kwargs) -> Any: ...

class PMSAvailabilityTool:
    def __init__(self, factory: PMSClientFactory): ...
    async def __call__(self, hotel_id, check_in, check_out, adults, children=0, babies=0,
                        rate_code="USD", room_type_filter="*ALL*", board_filter="*ALL*"):
        client = PMSClientFactory.create("minihotel", **self._creds_for(hotel_id))
        return client.get_availability(...)


MiniHotel first; the registry hides which PMS client was used.

Holiday/Calendar tools implement a common interface (HolidayProvider, CalendarFinder).

5) Conversation State & Diff-to-Replan
class StateRepository:
    def load(self, session_id: str) -> ConversationState: ...
    def save(self, session_id: str, state: ConversationState) -> None: ...

class StateDiff:
    @staticmethod
    def from_user_update(state: ConversationState, new_slots: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute changed constraints (dates/party/prefs), mark stale tool results,
        and signal Planner to refresh specific steps only.
        """


If the guest changes dates, invalidate cached availability only; keep room types, features, policies.

6) NLG (safe, sales-oriented, price-aware)
class NLG:
    def compose(self, state: ConversationState, tool_results: Dict[str, Any]) -> str:
        """
        Uses templates + LLM for tone. Prices inserted *only* from tool_results.
        If price missing or stale, show “Fetching price...” or ask to refine.
        """


“Critical rule” baked into policy.py: any {PRICE_*} placeholder must be replaced only from PMSAvailability or omitted.

7) Intent Router (micro-flows)
class IntentRouter:
    def route(self, state: ConversationState, parse: Dict[str,Any]) -> Intent:
        # E.g., "What about the next holiday weekend?" -> FIND_HOLIDAY
        # "Show me any two weeks in June" -> FIND_FLEXIBLE
        # "What’s included?" -> FAQ_POLICY

8) Channel Adapters

WhatsApp: webhook → normalize to InboundMessage → Orchestrator.

Web: chat widget + optional rich cards (room photos from RoomTypeCatalog).

Voice: ASR front → same normalized message; TTS for replies.
All channels share the same session_id and ConversationState.

Example Plans
A) “Next weekend, king bed, 2 nights”
{
  "steps": [
    {"id": "A", "tool": "calendar.resolve_next_weekend", "args": {"tz": "Asia/Jerusalem"}, "needs": [], "provides": ["stay.check_in","stay.check_out"], "parallelizable": false},
    {"id": "B", "tool": "pms.get_availability", "args": {"hotel_id":"H1","adults":2,"children":0}, "needs": ["stay.check_in","stay.check_out"], "provides": ["availability"]},
    {"id": "C", "tool": "pms.get_room_types", "args": {"hotel_id":"H1"}, "needs": [], "provides": ["room_types"]}
  ],
  "synthesis_hint": "Show cheapest King options; offer premium upsell if balcony/view exists"
}


Parallelism: B waits for dates; C can run immediately.

B) “Two families, flexible week in late March; else next free weekend”

Planner emits a branchless multi-probe plan; Runtime executes probes in parallel and returns the best feasible set:

Generate candidate windows: March 18–25, March 19–26, … (sliding week).

For each, call pms.get_availability in parallel (capped concurrency).

In parallel, probe calendar.find_next_free_weekend.

Synthesis ranks feasible options by total price and occupancy fit.

Integrating Your PMS Abstraction

You already have:

PMSClientFactory, get_room_types, get_rooms, get_availability, generate_booking_link.

Standard exceptions (PMSConnectionError, …).

Adapters (thin) just wrap these into tool functions + schemas. Example:

class GenerateBookingLinkTool:
    def __init__(self, factory: PMSClientFactory): self.factory = factory
    def __call__(self, hotel_id, check_in, check_out, adults, children=0, babies=0,
                 room_type_code=None, rate_code=None, board_code=None, **kw):
        client = self.factory.create("minihotel", **self._creds(hotel_id))
        return client.generate_booking_link(
            check_in=check_in, check_out=check_out, adults=adults, children=children,
            babies=babies, room_type_code=room_type_code, rate_code=rate_code,
            board_code=board_code, **kw
        )

Algorithms & Rules You’ll Want
Flexible Date Resolution

“Next weekend”: compute next Sat–Mon / Fri–Sun windows in local tz.

“Two weeks in June”: generate contiguous 14-night windows from June 1–30, stride 1 day, cap N candidates (e.g., 10).

“Christmas period”/named holidays: resolve via HolidayProvider then expand to 2–5 canonical windows (pre, during, post).

Multi-room/Families Fitter

Convert parties to room demands using RoomTypeAvailability.max_adults/children and occupancy_limits if present.

First-fit descent: try to pack families into minimal number of rooms honoring “connecting=true” when requested.

If not feasible: propose split strategies (e.g., 1 Family Suite + 1 Double with rollaway).

Price & Policy

Never fabricate price: only show totals from AvailabilityResponse.prices.

When comparing options, compute per-night on the fly from totals—but label clearly (“total vs X nights”).

Track currency and pass through to NLG templates.

Error Handling & Guardrails

Map PMS exceptions to user-safe messages (and logging detail server-side).

Timeouts & retries in Runtime; if one probe fails, synthesize with partial results.

PII: collect name/phone/email only; no payment in chat → always hand off via generate_booking_link.

Audit Log: store plan, tool calls, and raw tool results for testability.

Caching Strategy

Static: pms.get_room_types, get_rooms (daily TTL; manual bust on deploy).

Dynamic: never cache get_availability or prices.

Memoization per turn: when recomputing during a turn, reuse results by args hash.

Testing (conversation-driven)

Turn each example in chat_conversations.md into an executable trace test:

class ConversationTestCase(TypedDict):
    messages: List[str]
    expected_plan_shaped: List[str]  # e.g., ["calendar.resolve_next_weekend", "pms.get_availability", ...]
    expected_calls: List[ToolExpectation]  # tool name + args matcher
    expected_reply_contains: List[str]     # key phrases (NO hardcoded prices)
    must_not_hallucinate_price: bool


Golden traces: serialize plan + tool I/O; diff on regressions.

Mutation tests: change dates mid-flow → ensure StateDiff triggers replan only for availability.

Deployment & Observability

API: /chat (POST) → orchestrator; channel adapters call this.

Store: Postgres for conversations/tests; Redis for cache.

Metrics: latency per plan step, success rate by intent, price insertion rate (should always be 100% when a price is shown), tool error rates.

Tracing: plan id → step ids → tool spans.

Example End-to-End Handlers (condensed pseudocode)
async def handle_message(session_id: str, text: str, channel: str) -> str:
    state = repo.load(session_id) or ConversationState(booking=BookingContext(hotel_id="H1", parties=[GuestParty(adults=2)]))
    parse  = nlu.parse(text, state)
    intent = router.route(state, parse)
    plan   = planner.build(intent, parse["slots"], state)

    # Execute with parallelism
    plan_results = await runtime.execute(plan, tool_registry, ctx={"state": state})
    state.last_tool_results = plan_results

    # Update state (booking constraints, prices, options)
    state = reduce_state_with_results(state, plan_results)
    repo.save(session_id, state)

    # Policy: no price hallucination
    policy.assert_safe_prices(state, plan_results)

    # Compose reply
    reply = nlg.compose(state, plan_results)
    return reply

Booking Link Generation Flow

Guest confirms an option → Intent.GENERATE_LINK.

Planner emits a single pms.generate_booking_link step using the confirmed state (dates, party, selected room, rate/board).

NLG replies with the URL + concise summary (dates, room type, total price, cancellation note).

Channel Nuances

WhatsApp: keep messages short; include link preview; avoid inline tables.

Web: can render a small “options” card grid (images from room_types.image_url).

Voice: keep sentences concise; offer to send link by SMS.

Security Notes

Execution layer is sandboxed; tools are whitelisted with schemas.

Tool outputs are validated; unknown fields ignored.

Credentials for PMS per-hotel are stored encrypted; fetched by adapter per call.

Why this mirrors Claude-Code’s strengths

First-layer agent focuses on reasoning/planning; tools encapsulate side-effects.

MCP-style registry cleanly separates capabilities, letting you add/replace providers. 
Claude Docs
+1

Parallel, plan-then-act loops (ReAct-like) minimize latency and support quick re-planning when the guest changes their mind; sub-agents are a natural extension if you want specialized planners later (e.g., one for families, one for last-minute). 
arXiv
+1

Next Steps You Can Implement Immediately

Scaffold the modules above; wire the Tool Registry to your PMSClientFactory.

Implement Calendar/holiday tools (simple rules first; swap in a real provider later).

Ship minimal intents: CHECK_AVAILABILITY, FIND_FLEXIBLE, GENERATE_LINK.

Convert your sample chats into golden test cases and run in CI.

Add parallel availability probing for flexible windows.

Layer in policies (price safety) and telemetry.

If you want, I can turn this into a starter repo layout with stub classes and a couple of working planners (incl. “next weekend” and “two-week” flows).