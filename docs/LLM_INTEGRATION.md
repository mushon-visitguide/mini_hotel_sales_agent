# LLM-Based Intent Detection & Action Planning

This document describes the LLM-based intent detection system that replaced regex-based pattern matching.

## Overview

The system uses **OpenAI GPT-4 with Structured Outputs** to:
1. Extract user intent from natural language
2. Extract booking parameters (dates, guests, preferences)
3. Generate executable action plans
4. Execute tools in parallel where possible

## Architecture

```
User Message
    ↓
[LLM Intent Extractor] ← prompts/intent_extractor.yaml
    ↓ {intent, slots, confidence, reasoning}
[Action Planner] ← prompts/action_plans/*.yaml
    ↓ ActionPlan {actions: [{tool, args, parallel}]}
[Tool Executor] (parallel where possible)
    ↓ Results
Response
```

## Key Features

### ✅ 100% Reliable JSON
- Uses OpenAI Structured Outputs
- Guaranteed schema adherence
- No validation/retry needed

### ✅ Natural Language Understanding
- Handles variations ("next weekend", "this Friday", "under ₪500")
- Extracts complex parameters (children ages, budget, preferences)
- Provides reasoning for classifications

### ✅ Parallel Execution
- Actions marked as `parallel: true` execute concurrently
- Reduces latency significantly
- Example: FAQ + PMS calls run simultaneously

### ✅ Versioned Prompts
- All prompts in YAML files
- Version controlled
- Easy to test and iterate

## File Structure

```
hotel_sales_ai_agent/
├── prompts/
│   ├── system/
│   │   └── system.yaml                    # Base system prompt
│   ├── intent_extractor.yaml              # Intent detection prompt
│   └── action_plans/
│       ├── check_availability.yaml        # Availability search actions
│       ├── get_room_info.yaml             # Room information actions
│       └── generate_link.yaml             # Booking link actions
│
├── agent/
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py                      # OpenAI API wrapper
│   │   ├── schemas.py                     # Pydantic models
│   │   └── intent_extractor.py            # LLM intent extractor
│   │
│   ├── core/
│   │   ├── orchestrator.py                # Main orchestrator (UPDATED)
│   │   └── planner.py                     # Action planner (NEW)
│   │
│   └── tests/
│       └── test_llm_intent.py             # LLM tests
```

## Setup

### 1. Install Dependencies

```bash
pip install openai pydantic pyyaml
```

### 2. Set OpenAI API Key

```bash
export OPENAI_API_KEY="sk-..."
```

### 3. Verify Prompts Directory

Ensure `prompts/` folder exists at project root with all YAML files.

## Usage

### Basic Usage

```python
from agent.core.orchestrator import Orchestrator

# Create orchestrator with LLM
orchestrator = Orchestrator.create_default()

# Process user message
result = await orchestrator.process_message(
    message="Looking for a room next weekend for 2 adults",
    pms_type="minihotel",
    pms_username="user",
    pms_password="pass",
    hotel_id="wayinn",
    debug=True  # Enable debug output
)

print(f"Intent: {result['intent']}")
print(f"Confidence: {result['confidence']}")
print(f"Results: {result['results']}")
```

### With Custom Configuration

```python
from agent.llm import LLMClient, IntentExtractor
from agent.core.planner import ActionPlanner
from agent.core.orchestrator import Orchestrator

# Custom LLM client
llm_client = LLMClient(
    api_key="sk-...",
    model="gpt-4o-2024-08-06"  # Or other model
)

# Custom intent extractor
intent_extractor = IntentExtractor(
    llm_client=llm_client,
    prompts_dir="./prompts"
)

# Custom action planner
action_planner = ActionPlanner(
    action_plans_dir="./prompts/action_plans"
)

# Create orchestrator
orchestrator = Orchestrator(
    intent_extractor=intent_extractor,
    action_planner=action_planner
)
```

## Intent Types

### CHECK_AVAILABILITY
User wants to search for available rooms.

**Examples:**
- "Looking for a room next weekend"
- "Do you have availability?"
- "2 adults, 1 child for this Friday"

**Actions:**
- Get room types from FAQ (parallel)
- Check PMS availability (parallel)

### GET_ROOM_INFO
User asking about room types or amenities.

**Examples:**
- "What rooms do you have?"
- "Tell me about your suites"

**Actions:**
- Get room information from FAQ

### GENERATE_LINK
User wants a booking link.

**Examples:**
- "Send me a booking link"
- "I want to book now"

**Actions:**
- Generate booking URL from PMS

### COMPARE_OPTIONS
User comparing different rooms.

**Examples:**
- "What's the difference between X and Y?"
- "Compare the suites"

**Actions:**
- Get room information from FAQ

### GENERAL_QUESTION
Questions about policies, location, etc.

**Examples:**
- "What time is check-in?"
- "Do you allow pets?"

**Actions:**
- Get FAQ information

## Extracted Parameters (Slots)

### Dates
- `check_in`: YYYY-MM-DD format
- `check_out`: YYYY-MM-DD format
- `date_hint`: Fuzzy reference ("next weekend")

### Party Composition
- `adults`: Number of adults (default: 2)
- `children`: Array of ages [5, 7, 12]

### Preferences
- `budget_max`: Maximum price
- `currency`: USD, ILS, or EUR
- `board_preference`: Meal plan preference
- `bed_preference`: Bed configuration

## Action Plans

Action plans are YAML templates that define which tools to call for each intent.

### Example: check_availability.yaml

```yaml
intent: CHECK_AVAILABILITY
description: Search for available rooms

actions:
  - id: get_room_types
    tool: faq.get_rooms_and_pricing
    args: {}
    parallel: true  # Runs concurrently

  - id: check_availability
    tool: pms.get_availability
    args:
      check_in: "${slots.check_in}"        # Filled from extracted slots
      check_out: "${slots.check_out}"
      adults: "${slots.adults}"
      children: "${calc.children_count}"   # Calculated value
      babies: "${calc.babies_count}"
      rate_code: "${slots.currency}"
    parallel: true  # Runs concurrently

synthesis_hint: "present_top_options"
```

### Variable Substitution

Templates support `${variable}` placeholders:

- `${slots.field}` - Extracted parameters
- `${calc.field}` - Calculated values
- `${credentials.field}` - PMS credentials

## Date Resolution

Fuzzy date hints are automatically resolved to actual dates:

| Hint            | Resolution                      |
|-----------------|---------------------------------|
| "next weekend"  | Next Friday-Sunday              |
| "this weekend"  | Upcoming Friday-Sunday          |
| "next week"     | 7 days from today (2 nights)    |

Timezone: **Asia/Jerusalem**

## Children vs Babies

Children are automatically split by age:
- **Babies**: Ages 0-1
- **Children**: Ages 2-17

Example:
```
Input: "kids ages 1, 5, 8"
Output: babies=1, children=2
```

## Parallel Execution

Actions with `parallel: true` execute concurrently using `asyncio.gather()`.

**Example:**
```python
# These run simultaneously
parallel_actions = [
    {"tool": "faq.get_rooms_and_pricing", "parallel": true},
    {"tool": "pms.get_availability", "parallel": true}
]

# Result: ~500ms instead of ~1000ms (50% faster)
```

## Testing

### Run Tests

```bash
# Set API key
export OPENAI_API_KEY="sk-..."

# Run LLM intent tests
pytest agent/tests/test_llm_intent.py -v

# Run with debug output
pytest agent/tests/test_llm_intent.py -v -s
```

### Manual Testing

```bash
# Run manual test script
cd agent/tests
python test_llm_intent.py
```

## Cost & Performance

### Cost per Request
- **Model**: GPT-4o-2024-08-06
- **Cost**: ~$0.01 per intent extraction
- **Can be reduced**: Cache common queries

### Latency
- **Intent Extraction**: 500-800ms
- **Total (with tools)**: 1-2 seconds
- **Parallel execution**: 30-50% faster than sequential

### Reliability
- **Schema Adherence**: 100% (Structured Outputs)
- **Intent Accuracy**: ~95% (with good prompts)
- **No validation needed**: Model guarantees valid JSON

## Prompt Engineering Tips

### 1. Add More Examples
Edit `prompts/intent_extractor.yaml` and add examples:

```yaml
examples:
  - user: "Your example message"
    output:
      intent: {...}
      slots: {...}
      reasoning: "..."
```

### 2. Adjust Confidence Threshold
Filter low-confidence results:

```python
if result.intent.confidence < 0.7:
    # Ask clarifying question
    pass
```

### 3. Add New Intents
1. Add to `schemas.py` Intent enum
2. Add to `prompts/intent_extractor.yaml` descriptions
3. Create action plan YAML (optional)

## Debugging

### Enable Debug Output

```python
result = await orchestrator.process_message(
    message="...",
    debug=True  # Shows intent, slots, actions, tool calls
)
```

### Check LLM Reasoning

```python
print(result['reasoning'])
# "User wants to search for rooms with specific dates..."
```

### Inspect Extracted Slots

```python
print(result['slots'])
# {'date_hint': 'next weekend', 'adults': 2, ...}
```

## Migration from Regex

The old regex-based system has been completely replaced:

| Old (Regex)              | New (LLM)                          |
|--------------------------|------------------------------------|
| `detect_intent()`        | `intent_extractor.extract()`       |
| `build_plan()`           | `action_planner.plan()`            |
| Hardcoded patterns       | Learned from examples              |
| String matching          | Natural language understanding     |
| Manual date parsing      | Automatic fuzzy date resolution    |

## Troubleshooting

### "OpenAI API key not found"
```bash
export OPENAI_API_KEY="sk-..."
```

### "Prompt file not found"
Ensure `prompts/` directory exists at project root:
```bash
ls prompts/intent_extractor.yaml
```

### "Schema validation error"
Check `agent/llm/schemas.py` - ensure fields match prompt examples.

### Low confidence scores
Add more examples to `prompts/intent_extractor.yaml` for that intent type.

## Advanced: Custom Models

You can use other OpenAI models or even local models:

```python
llm_client = LLMClient(
    model="gpt-4o-mini-2024-07-18"  # Cheaper, faster
)
```

**Note**: Structured Outputs only works with these models:
- `gpt-4o-2024-08-06`
- `gpt-4o-mini-2024-07-18`

## Future Enhancements

- [ ] Add conversation history context
- [ ] Implement confidence-based fallbacks
- [ ] Add multilingual support
- [ ] Cache common queries to reduce cost
- [ ] Add A/B testing for prompts
- [ ] Implement reasoning traces

## Resources

- [OpenAI Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [YAML Specification](https://yaml.org/spec/)

---

For questions or issues, see the main README.md
