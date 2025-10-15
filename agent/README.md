# Hotel Sales AI Agent - Tool System

## Overview

This is a **tool-based AI agent system** for hotel booking automation. The agent receives messages, detects intent, and executes PMS (Property Management System) tools to fetch availability, generate booking links, etc.

## Architecture

```
Message → Orchestrator → Intent Detection → Plan Building → Tool Execution → Results
```

### Components

1. **Tool Registry** (`agent/tools/registry.py`)
   - Decorator-based tool registration: `@registry.tool()`
   - Auto-generates Pydantic schemas from function type hints
   - Validates inputs and redacts sensitive fields in logs

2. **PMS Tools** (`agent/tools/pms/tools.py`)
   - `pms.get_availability` - Real-time room availability and pricing
   - `pms.generate_booking_link` - Booking URL generation
   - Each tool receives credentials as parameters (stateless)

3. **FAQ Tools** (`agent/tools/faq/tools.py`)
   - `faq.get_rooms_and_pricing` - Static room type information and pricing details
   - `faq.get_policies_and_procedures` - Hotel policies and procedures
   - `faq.get_facilities_and_services` - Facilities, services, and location info
   - `faq.get_my_stay_guide` - Guest stay guide (WiFi, door codes, troubleshooting)
   - No credentials required (static information)

4. **Orchestrator** (`agent/core/orchestrator.py`)
   - Receives message + hotel credentials
   - Detects intent using keyword matching
   - Builds execution plan
   - **Prints plan before execution** (with redacted credentials)
   - Executes tools via registry
   - Returns structured results

## Quick Start

### Installation

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install pydantic pytest-asyncio
```

### Running Tests

```bash
# Run all tests
pytest agent/tests/test_orchestrator.py -v

# Run with output (shows plan printing)
pytest agent/tests/test_orchestrator.py -v -s

# Run specific test
pytest agent/tests/test_orchestrator.py::TestOrchestrator::test_process_availability_message -v -s
```

### Test Results

✅ **All 11 tests passing**

- ✅ Intent detection (3/3)
- ✅ Plan building (3/3)
- ✅ Availability check with real MiniHotel API
- ✅ Room types from FAQ (static information)
- ✅ Booking link generation
- ✅ Conversation flow
- ✅ Error handling

## Usage Example

```python
from agent.core.orchestrator import Orchestrator

# Create orchestrator
orchestrator = Orchestrator()

# Process message with hotel credentials
result = await orchestrator.process_message(
    message="Looking for a room next weekend",
    pms_type="minihotel",
    pms_username="visitguide",
    pms_password="visg#!71R",
    hotel_id="wayinn",
    pms_use_sandbox=False
)

# Output shows:
# [Orchestrator] Intent: CHECK_AVAILABILITY
# [Orchestrator] Plan: pms.get_availability
# [Orchestrator] Executing tool...
# [Orchestrator] Completed successfully
```

## Creating New Tools

Adding a new tool is simple with the decorator pattern:

```python
from agent.tools.registry import registry
from typing import Optional

@registry.tool(
    name="my_tool",
    description="Does something useful",
    redact=["sensitive_field"]
)
async def my_tool_function(
    required_param: str,
    optional_param: Optional[int] = None
) -> dict:
    """Your tool implementation"""
    # Do work here
    return {"result": "data"}
```

The tool is automatically:
- Registered in the global registry
- Schema-validated (Pydantic)
- Logged with sensitive field redaction
- Available to the orchestrator

## Project Structure

```
agent/
├── core/
│   ├── orchestrator.py       # Main orchestrator
│   └── __init__.py
├── tools/
│   ├── registry.py           # @tool decorator + ToolRegistry
│   ├── pms/
│   │   ├── tools.py          # PMS tool functions
│   │   └── __init__.py
│   ├── faq/
│   │   ├── tools.py          # FAQ tool functions
│   │   └── __init__.py
│   └── __init__.py
├── tests/
│   ├── test_orchestrator.py  # Integration tests
│   └── __init__.py
└── README.md                  # This file
```

## Key Features

### 1. Decorator-Based Tools
- Minimal boilerplate
- Type-safe with Pydantic validation
- Auto-generated schemas

### 2. Stateless Design
- Tools receive all needed params (including credentials)
- No global state
- Easy to test

### 3. Plan Printing
- Shows which tools will be called **before execution**
- Redacts sensitive data (username, password)
- Helps with debugging and transparency

### 4. Real PMS Integration
- Works with MiniHotel production API
- Tested with "The Way Inn" hotel (wayinn)
- Supports EzGo as well

## Test Credentials

The tests use "The Way Inn" hotel credentials:

```python
PMS_TYPE = "minihotel"
PMS_USERNAME = "visitguide"
PMS_PASSWORD = "visg#!71R"
HOTEL_ID = "wayinn"
USE_SANDBOX = False  # Production mode
```

## Next Steps

1. **Add LLM-based NLU** - Replace keyword matching with LLM intent detection
2. **Add date resolution** - Parse "next weekend" → actual dates
3. **Add NLG** - Generate natural language responses from tool results
4. **Add state management** - Track conversation context
5. **Add more tools** - FAQ, room comparison, etc.

## Design Philosophy

- **Separation of concerns**: Tools, orchestration, and presentation are separate
- **Testability**: Each component has clear inputs/outputs
- **Extensibility**: Add new tools without changing core code
- **Observability**: Plans are printed and logged
- **Safety**: Sensitive data is redacted in logs
- **Type safety**: Pydantic validation throughout

## Contributing

To add a new tool:
1. Create function in `agent/tools/[category]/`
2. Add `@registry.tool()` decorator
3. Import in `agent/tools/[category]/__init__.py`
4. Add tests in `agent/tests/`

That's it! The tool is automatically registered and available.
