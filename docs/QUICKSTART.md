# Quick Start Guide

## Setup

1. **Activate virtual environment:**
```bash
source venv/bin/activate
```

2. **Load environment variables:**
```bash
source .env
```

3. **Set PYTHONPATH:**
```bash
export PYTHONPATH=/home/mushon/hotel_sales_ai_agent:$PYTHONPATH
```

## Run Interactive Agent

```bash
python main.py
```

## Example Conversation

```
You: Looking for a room next weekend for 2 adults

📋 PLANNING & EXECUTION
======================================================================

[ToolPlanner] Planning for: 'Looking for a room next weekend for 2 adults'
[ToolPlanner] Action: Search for available rooms for 2 adults next weekend
[ToolPlanner] Tools (2):
  - get_room_info: faq.get_rooms_and_pricing (parallel)
  - check_availability: pms.get_availability (parallel)

[Runtime] Executing 2 tools
[Runtime] Organized into 1 waves
  Wave 1: ['faq.get_rooms_and_pricing', 'pms.get_availability']

[Runtime] Executing wave 1/1 (2 tools in parallel)
  [Tool] get_room_info completed
  [Tool] check_availability completed

📊 RESULT SUMMARY
======================================================================

🎯 Action: Search for available rooms for 2 adults next weekend

💭 Reasoning: User wants to search for rooms for next weekend, so I'm
   calling FAQ for room info and PMS for real-time availability. Both
   can run in parallel.

🔧 Tools Executed: 2
  ✅ get_room_info
  ✅ check_availability

📦 Slots Extracted:
  - date_hint: next weekend
  - adults: 2

📋 Results:
  ✅ get_room_info: {...room information...}
  ✅ check_availability: {...availability data...}
```

## Try These Messages

- "What rooms do you have?"
- "Looking for a room next weekend"
- "Family of 4, kids ages 5 and 8"
- "Send me a booking link"
- "What's the check-in time?"
- "Looking for room under ₪500"

## What's Happening

1. **LLM Planning**: OpenAI GPT-4o analyzes your message and creates a tool execution plan
2. **Tool Selection**: LLM dynamically chooses which tools to call (no hardcoded intents!)
3. **Parallel Execution**: Independent tools run simultaneously for speed
4. **Real APIs**: Calls real MiniHotel PMS API for availability and pricing

## Architecture

```
User Message → ToolPlanner (LLM) → Runtime (DAG Executor) → Results
                    ↓
            Natural Language Action
            + Extracted Slots
            + Tools DAG with dependencies
```

## Key Features

- ✅ **No Hardcoded Intents** - LLM decides everything dynamically
- ✅ **Parallel Execution** - Independent tools run simultaneously
- ✅ **DAG Support** - Tools can depend on other tools
- ✅ **Real APIs** - No mocks, everything is live
- ✅ **Natural Language Actions** - Human-readable action descriptions

## Run Tests

```bash
# Run all tests
pytest agent/tests/ -v

# Run specific test suite
pytest agent/tests/test_llm_intent.py -v

# Run with output
pytest agent/tests/test_orchestrator.py -v -s
```

## Environment Variables

Required in `.env`:
```bash
export OPENAI_API_KEY=sk-...
export MINIHOTEL_USERNAME=...
export MINIHOTEL_PASSWORD=...
```
