# Quick Start: LLM-Based Intent Detection

Get started with the LLM-based hotel booking assistant in 5 minutes.

## Prerequisites

```bash
# 1. Install dependencies
pip install openai pydantic pyyaml

# 2. Set your OpenAI API key
export OPENAI_API_KEY="sk-your-key-here"
```

## Basic Usage

### 1. Simple Intent Extraction

```python
from agent.llm import LLMClient, IntentExtractor

# Create LLM client
llm_client = LLMClient()

# Create intent extractor
intent_extractor = IntentExtractor(
    llm_client=llm_client,
    prompts_dir="./prompts"
)

# Extract intent from user message
result = intent_extractor.extract("Looking for a room next weekend")

print(f"Intent: {result.intent.name}")
print(f"Confidence: {result.intent.confidence}")
print(f"Dates: {result.slots.date_hint}")
print(f"Guests: {result.slots.adults} adults")
print(f"Reasoning: {result.reasoning}")
```

**Output:**
```
Intent: CHECK_AVAILABILITY
Confidence: 0.95
Dates: next weekend
Guests: 2 adults
Reasoning: User wants to search for available rooms with specific dates...
```

### 2. Full Orchestrator (E2E)

```python
import asyncio
from agent.core.orchestrator import Orchestrator

async def main():
    # Create orchestrator (one-liner!)
    orchestrator = Orchestrator.create_default()

    # Process user message
    result = await orchestrator.process_message(
        message="2 adults and a 5 year old for this Friday",
        pms_type="minihotel",
        pms_username="visitguide",
        pms_password="visg#!71R",
        hotel_id="wayinn",
        pms_use_sandbox=False,
        debug=True  # See what's happening
    )

    # Results include:
    print(f"\nIntent: {result['intent']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Extracted params: {result['slots']}")
    print(f"Actions executed: {result['actions']}")
    print(f"Results: {result['results'].keys()}")

asyncio.run(main())
```

## Understanding the Output

The orchestrator returns a structured result:

```python
{
    "intent": "CHECK_AVAILABILITY",           # Detected intent
    "confidence": 0.95,                        # How confident (0-1)
    "reasoning": "User wants to search...",    # Why this intent
    "slots": {                                 # Extracted parameters
        "date_hint": "this Friday",
        "adults": 2,
        "children": [5],
        "currency": "ILS"
    },
    "actions": [                               # Tools that were called
        "get_room_types",
        "check_availability"
    ],
    "results": {                               # Tool outputs
        "get_room_types": {...},
        "check_availability": {...}
    },
    "synthesis_hint": "present_top_options"   # How to format response
}
```

## Testing Different Intents

### Check Availability
```python
messages = [
    "Looking for a room next weekend",
    "2 adults for this Friday-Saturday",
    "Family of 4 (kids 5 and 8) need a room",
]
```

### Get Room Information
```python
messages = [
    "What rooms do you have?",
    "Tell me about your suites",
    "Room types and amenities?",
]
```

### Generate Booking Link
```python
messages = [
    "Send me a booking link",
    "I want to book now",
    "How do I reserve?",
]
```

### With Budget
```python
messages = [
    "Room under ₪500",
    "Max $200 per night",
    "Around €150",
]
```

## Common Patterns

### Pattern 1: Extract + Validate

```python
# Extract intent
result = intent_extractor.extract(user_message)

# Check confidence
if result.intent.confidence < 0.7:
    print("Not sure what you mean. Can you rephrase?")
    exit()

# Validate required fields
if result.intent.name == "CHECK_AVAILABILITY":
    if not result.slots.date_hint and not result.slots.check_in:
        print("When would you like to stay?")
```

### Pattern 2: Action Planning

```python
from agent.core.planner import ActionPlanner

# Create planner
planner = ActionPlanner(action_plans_dir="./prompts/action_plans")

# Get intent
intent_result = intent_extractor.extract(message)

# Create action plan
plan = planner.plan(
    intent_result=intent_result,
    credentials={"pms_type": "minihotel", ...}
)

# Inspect plan
print(f"Will execute {len(plan.actions)} actions:")
for action in plan.actions:
    print(f"  - {action['tool']} (parallel={action['parallel']})")
```

### Pattern 3: Parallel Execution

```python
# The orchestrator automatically runs parallel actions concurrently
result = await orchestrator.process_message(message, ...)

# check_availability.yaml defines:
# - get_room_types (parallel: true)
# - check_availability (parallel: true)

# Both run simultaneously → 50% faster!
```

## Customizing Prompts

### Add Examples

Edit `prompts/intent_extractor.yaml`:

```yaml
examples:
  - user: "Your custom example"
    output:
      intent:
        name: "CHECK_AVAILABILITY"
        confidence: 0.9
      slots:
        date_hint: "next weekend"
      reasoning: "User wants to search..."
```

### Change System Prompt

Edit `prompts/system/system.yaml`:

```yaml
prompt: |
  You are a helpful hotel booking assistant.
  [Your custom instructions here]
```

### Add New Intent

1. Edit `agent/llm/schemas.py`:
```python
class Intent(BaseModel):
    name: Literal[
        "CHECK_AVAILABILITY",
        "GET_ROOM_INFO",
        "YOUR_NEW_INTENT",  # Add here
        ...
    ]
```

2. Add to `prompts/intent_extractor.yaml`:
```yaml
YOUR_NEW_INTENT:
  - Description of when to use this intent
  - Examples...
```

3. Create action plan (optional):
```yaml
# prompts/action_plans/your_new_intent.yaml
intent: YOUR_NEW_INTENT
actions:
  - id: some_action
    tool: some.tool
    args: {...}
```

## Debugging

### Enable Debug Mode

```python
result = await orchestrator.process_message(
    message="...",
    debug=True  # Shows everything
)
```

You'll see:
- Intent extraction (intent, confidence, reasoning)
- Extracted parameters (slots)
- Action plan (which tools, which args)
- Tool execution (start, complete)

### Check Reasoning

```python
result = intent_extractor.extract(message)
print(result.reasoning)
# "User explicitly requests booking link based on phrase 'send me a link'"
```

### Inspect Slots

```python
print(result.slots.dict(exclude_none=True))
# {'date_hint': 'next weekend', 'adults': 2, 'children': [5], 'currency': 'ILS'}
```

## Tips

### 💡 Tip 1: Start Simple
Begin with basic queries and gradually add complexity.

### 💡 Tip 2: Check Confidence
Always check `result.intent.confidence`. If < 0.7, ask clarifying questions.

### 💡 Tip 3: Use Parallel Actions
Mark independent actions as `parallel: true` in action plans for better performance.

### 💡 Tip 4: Cache Common Queries
Store results for common queries to save API costs.

### 💡 Tip 5: Monitor Costs
GPT-4o costs ~$0.01 per intent extraction. Track usage in production.

## Common Issues

### "OpenAI API key not found"
```bash
export OPENAI_API_KEY="sk-..."
```

### "Prompt file not found"
Make sure you're running from project root where `prompts/` exists.

### "Model not found"
Structured Outputs requires:
- `gpt-4o-2024-08-06` (default)
- `gpt-4o-mini-2024-07-18`

### Low Confidence Scores
Add more examples to `prompts/intent_extractor.yaml`.

## Next Steps

1. **Read LLM_INTEGRATION.md** - Full documentation
2. **Run tests** - `pytest agent/tests/test_llm_intent.py -v`
3. **Customize prompts** - Add your examples
4. **Add new intents** - Extend the system
5. **Optimize costs** - Implement caching

## Example Scripts

### Test Suite

```bash
# Install dependencies
pip install pytest pytest-asyncio

# Run tests
export OPENAI_API_KEY="sk-..."
pytest agent/tests/test_llm_intent.py -v -s
```

### Interactive Testing

```python
# interactive_test.py
import asyncio
from agent.core.orchestrator import Orchestrator

async def interactive():
    orchestrator = Orchestrator.create_default()

    while True:
        message = input("\n💬 You: ")
        if message.lower() in ['exit', 'quit']:
            break

        result = await orchestrator.process_message(
            message=message,
            pms_type="minihotel",
            pms_username="visitguide",
            pms_password="visg#!71R",
            hotel_id="wayinn",
            debug=False
        )

        print(f"\n🤖 Intent: {result['intent']}")
        print(f"   Confidence: {result['confidence']:.2f}")
        print(f"   Slots: {result['slots']}")

asyncio.run(interactive())
```

## Resources

- **Full Docs**: `LLM_INTEGRATION.md`
- **OpenAI Structured Outputs**: https://platform.openai.com/docs/guides/structured-outputs
- **Pydantic**: https://docs.pydantic.dev/

---

Questions? Check `LLM_INTEGRATION.md` or the main `README.md`.
