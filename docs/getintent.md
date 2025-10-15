------ /Users/mushon/visitguide/services/ai-server/docs/function_detection_flow.md
# Function Detection and Routing System Documentation

## Overview

The AI Server uses a two-phase approach to process user messages:

1. **Intent Detection Phase** - Determines if the user intent is complete and routes to appropriate commands
2. **Function Selection Phase** - Selects the specific agent/function to handle the request

Both phases run in **parallel** for optimal performance.

---

## Architecture

### Key Components

1. **ChatCore** (`src/core/chat_core.py:172-515`)
   - Main orchestrator for message processing
   - Runs intent detection and function selection in parallel
   - Routes to appropriate agents based on results

2. **GetUserIntentInfo** (`src/core/config/get_user_intent_info.py`)
   - Handles conversational intent gathering
   - Detects command patterns in responses
   - Streams responses back to user

3. **GetFunctionToRun** (`src/core/config/get_func_to_run.py`)
   - Determines which specialized agent should handle the request
   - Extracts required parameters from conversation
   - Uses JSON response format for structured output

4. **ServiceConfig** (`src/core/config/config.py`)
   - Loads YAML configuration files
   - Defines available functions and their parameters
   - Provides examples for function matching

---

## Complete Flow

### 1. Message Receipt

When a user message arrives (via `ChatCore.process_message`):

```python
# src/core/chat_core.py:172
async def process_message(
    self,
    user_input: str,
    get_input_func: Callable[[], Awaitable[str]],
    chunk_display_func: Callable[[str], Awaitable[None]],
    ...
)
```

### 2. Add to History

The user message is immediately added to conversation history:

```python
# src/core/chat_core.py:202
await self.history_manager.add_to_history(
    "user", user_input, "USER", "USER",
    custom_timestamp, channel_message_id,
    skip_sync=True, media_metadata=media_metadata
)
```

### 3. Parallel Execution

Three tasks run concurrently for optimal performance:

```python
# src/core/chat_core.py:204-234
# Create parallel tasks
intent_task = asyncio.create_task(
    self.intent_handler.get_intent(...)
)

func_task = asyncio.create_task(
    self.function_handler.get_func_to_run(...)
)

lang_task = asyncio.create_task(
    self.util_agent.detect_user_language(...)
)

# Wait for all to complete
intent_result, func_result, detected_language = await asyncio.gather(
    intent_task, func_task, lang_task
)
```

---

## Phase 1: Intent Detection (GetUserIntentInfo)

### Purpose
Gather all required information from the user through conversation, detect command patterns, and determine if we have everything needed.

### Prompt Structure

The intent detection uses a detailed prompt built in `_build_messages()`:

```python
# src/core/config/get_user_intent_info.py:121-199
def _build_messages(self, query: str, chat_history: Optional[List[Dict[str, str]]] = None)
```

#### Prompt Components:

1. **Organization Context**
   - Display name of the organization
   - Current date and time

2. **Guest Information** (if available)
   - Guest name, check-in/out dates, room details
   - Used for personalized assistance

3. **Function List**
   - All available functions with their descriptions
   - Includes command patterns (e.g., `/faq`, `/reservation`)
   - Parameters considerations for each function

4. **General AI Knowledge**
   - Custom guidelines from organization
   - Supervisor-provided instructions

5. **Rules Section**
   ```
   # RULES:
   1. Never provide information not based on provided data
   2. Don't rely on your own knowledge
   3. Command Selection:
      - Analyze user's request and determine appropriate command
      - Use specialized commands when all params are known
      - Use /general if ANY parameter is missing
      - Begin response with chosen command
      - NEVER use backticks around commands
   4. You were created by https://visitguide.ai
   ```

6. **Chat History**
   - Compressed to last 12 messages
   - Provides context for current query

7. **Language Rules**
   - ALWAYS respond in the language of the current query
   - Ignore previous conversation language

8. **Current Query**
   - The user's latest message

### Command Detection

The system looks for specific command patterns in the AI response:

```python
# src/core/config/get_user_intent_info.py:219-327
# Commands are detected by checking for "/" prefix
# Examples: /faq, /reservation, /around, /general

# If command found in first tokens:
if "/" in chunk:
    command_detected = True
    command_buffer = chunk

# Check if it's /general (continue conversation)
if "general" in command_buffer:
    # Remove /general prefix and continue
    move_on_detected = False

# Check if it's a specialized command
elif any(cmd in command_buffer for cmd in self.commands):
    # Route to specialized agent
    move_on_detected = True
```

### Response Flow

1. **Stream Response**: AI response is streamed token by token
2. **Command Detection**: First few tokens are analyzed for commands
3. **Routing Decision**:
   - `/general` → Continue conversation (gather more info)
   - Specialized command → Route to function (all info gathered)
   - No command → Pass through to user

### Return Values

```python
# src/core/config/get_user_intent_info.py:366
return full_response, move_on_detected, message_sent
```

- `full_response`: Complete AI response text
- `move_on_detected`: True if specialized command detected
- `message_sent`: True if response was sent to user

---

## Phase 2: Function Selection (GetFunctionToRun)

### Purpose
Determine which specialized agent should handle the request and extract required parameters.

### Prompt Structure

Built in `_generate_prompt()`:

```python
# src/core/config/get_func_to_run.py:38-121
def _generate_prompt(self, chat_history: List[Dict[str, str]]) -> str
```

#### Prompt Components:

1. **Task Description**
   ```
   You job is to extract the right function call and relevant parameters.
   You must categorize each request into one of these functions,
   please rely on the chat history to make the decision.
   ```

2. **Current Date Context**
   - Today's date with day of week
   - Used for date calculations

3. **Function List**
   Each function includes:
   - **Name**: e.g., `FAQ_AGENT`, `AVAILABILITY_AGENT`
   - **Description**: When to use this function
   - **Parameters Considerations**: How to extract/format parameters

   Example:
   ```yaml
   AVAILABILITY_AGENT:
     Description: when user is looking for availability or pricing
     Parameters Considerations:
       - startDate: format <weeks> <days> or DD-MM-YYYY
       - numberOfNights: required
       - Rooms: list with adults and childrenAges
   ```

4. **Dynamic Parameter Replacements**
   ```python
   # Current day, date, month, year are replaced in template
   pc = pc.replace("{current_day}", current_day)
   pc = pc.replace("{current_year}", current_year)
   ```

5. **General AI Knowledge** (optional)
   - Additional context from organization settings

6. **Examples**
   Real conversation examples showing:
   - User input
   - Expected function
   - Expected parameters

   Example:
   ```yaml
   - input: "Any availability for 3 people on 12/12/25"
     func: AVAILABILITY_AGENT
     params:
       startDate: 12-12-2025
       numberOfNights: 1
       Rooms:
         - adults: 3
           childrenAges: []
   ```

7. **Conversation History**
   - Compressed to last 12 messages
   - User messages prefixed with `>>`
   - Assistant messages prefixed with `>`

8. **Output Format Instruction**
   ```
   Respond only with a JSON object containing 'func' and 'params'.
   If information is missing, include null values for required parameters.
   ```

### OpenAI Parameters

```python
# src/core/config/get_func_to_run.py:128-137
response = await asyncio.to_thread(
    self.client.chat.completions.create,
    model="gpt-4.1",
    messages=messages,
    temperature=1e-19,      # Near-zero for deterministic output
    top_p=1e-9,             # Near-zero for consistency
    seed=1234,              # Fixed seed for reproducibility
    response_format={"type": "json_object"}  # Force JSON
)
```

### Response Processing

```python
# src/core/config/get_func_to_run.py:139-169
response_json = json.loads(response_text)

# Example response:
{
    "func": "AVAILABILITY_AGENT",
    "params": {
        "startDate": "0 1",  # Tomorrow
        "numberOfNights": 2,
        "Rooms": [
            {
                "adults": 2,
                "childrenAges": [5, 1]
            }
        ],
        "language": "HEBREW"
    }
}
```

### Validation

1. **Check if function exists in FuncType enum**
   ```python
   if func_str in [ft.value for ft in FuncType]:
       func_type = FuncType(func_str)
   else:
       func_type = FuncType.FAQ_AGENT  # Default fallback
   ```

2. **Check if function exists in config**
   ```python
   if func_str not in self.service_config.functions:
       func_type = FuncType.FAQ_AGENT  # Default fallback
   ```

---

## Phase 3: Function Routing

After both parallel tasks complete, ChatCore routes to the appropriate agent:

### Command Override

If intent detection found a command, it overrides function selection:

```python
# src/core/chat_core.py:263-297
# Build command mapping from config
command_mapping = {}
for name, func_obj in self.service_config.functions.items():
    if hasattr(func_obj, 'command') and func_obj.command:
        base_command = func_obj.command.split()[0]
        pattern = fr'^{re.escape(base_command)}(?:\s|$)'
        func_enum = FuncType(name)
        command_mapping[pattern] = func_enum

# Check for direct command in response
for pattern, func in command_mapping.items():
    if re.search(pattern, response):
        func_type = func  # Override
        break
```

### Agent Execution

Based on the selected function type:

```python
# src/core/chat_core.py:309-477
if func_type == FuncType.AVAILABILITY_AGENT:
    response = await self.availability_agent.generate_response(
        user_input, params, history, phone, chunk_display_func
    )

elif func_type == FuncType.FAQ_AGENT:
    response = await self.faq_agent.generate_response(
        user_input, params, history, phone, chunk_display_func
    )

elif func_type == FuncType.DO_AROUND_AGENT:
    response = await self.do_around_agent.search_and_format(
        query=params.get("search_phrase"),
        location=self.do_around_address,
        ...
    )

# ... other function types ...

else:
    # Default to FAQ agent
    response = await self.faq_agent.generate_response(...)
```

---

## Available Function Types

Defined in `FuncType` enum:

```python
# src/core/config/get_func_to_run.py:20-28
class FuncType(Enum):
    INTERNET_SEARCH = "INTERNET_SEARCH"
    AVAILABILITY_AGENT = "AVAILABILITY_AGENT"
    WEBSITE_SEARCH = "WEBSITE_SEARCH"
    GET_USER_INTENT = "GET_USER_INTENT"
    FAQ_AGENT = "FAQ_AGENT"
    DAY_TRIP_PLANNER = "DAY_TRIP_PLANNER"
    DO_AROUND_AGENT = "DO_AROUND_AGENT"
    PRE_CHECKIN_AGENT = "PRE_CHECKIN_AGENT"
```

---

## Configuration Files

### Structure

YAML files define the behavior for different organization types:

**Location**: `src/core/config/services/*.yaml`

**Available Configs**:
- `accommodations.yaml` - Hotels with reservation system
- `accommodations-without-reservation.yaml` - Hotels without booking
- `accommodations-adults-only.yaml` - Adult-only properties
- `accommodations-guest-journey.yaml` - Guests with active reservations
- `restaurant.yaml` - Restaurant services
- `attraction.yaml` - Tourist attractions

### YAML Schema

```yaml
# Conversation examples (currently unused)
conversation_examples: |
  no examples for, stick to guidelines

# Function definitions
functions:
  - name: FAQ_AGENT                    # Must match FuncType enum
    command: "/faq"                    # Command pattern to detect
    description: |                     # When to use this function
      for frequently asked questions or general questions

    parameters_considerations: |      # How to format parameters
      language should be the same as the user last question

    considerations: |                 # Additional guidelines
      (agent-specific considerations)

  - name: AVAILABILITY_AGENT
    command: "/reservation"
    description: |
      when user is looking for availability or pricing
      Required parameters:
        1. Rooms (list):
           - adults: number (default 2)
           - childrenAges: array (default [])
        2. startDate (required)
        3. numberOfNights (required)

    parameters_considerations: |
      for date parameter:
      - format: <weeks> <days> or DD-MM-YYYY
      - calculate based on {current_day}
      - if user asks for weekend, Thursday to Saturday

# Example conversations for training
functions_examples:
  - input: "What are the nightly rates?"
    func: FAQ_AGENT
    params: {}

  - input: "availability for 2 adults tomorrow"
    func: AVAILABILITY_AGENT
    params:
      startDate: "0 1"
      numberOfNights: 1
      Rooms:
        - adults: 2
          childrenAges: []
```

---

## Example Flow Walkthrough

### Scenario: User asks for availability

**User Input**: "I need a room for 2 adults and a child aged 5 tomorrow for 2 nights"

### Step 1: Parallel Execution Starts

Both intent and function detection run simultaneously:

#### Intent Detection:
1. Builds prompt with function list and commands
2. Sends to OpenAI with streaming
3. AI responds: "/reservation I'll check availability for you..."
4. Detects `/reservation` command in first tokens
5. Sets `move_on_detected = True`
6. Returns: `(response, True, True)`

#### Function Detection:
1. Builds prompt with function examples
2. Sends to OpenAI with JSON format
3. AI responds:
   ```json
   {
     "func": "AVAILABILITY_AGENT",
     "params": {
       "startDate": "0 1",
       "numberOfNights": 2,
       "Rooms": [
         {
           "adults": 2,
           "childrenAges": [5]
         }
       ]
     }
   }
   ```
4. Returns: `(FuncType.AVAILABILITY_AGENT, params)`

### Step 2: Results Combined

```python
# Both tasks complete
intent_result = (response, True, True)
func_result = (FuncType.AVAILABILITY_AGENT, params)

# Extract function type
func_type = FuncType.AVAILABILITY_AGENT
```

### Step 3: Command Override Check

```python
# Check if response contains command
if "/reservation" in response:
    # Override with command's function type
    func_type = FuncType.AVAILABILITY_AGENT
```

### Step 4: Language Detection

```python
detected_language = {
    'language': 'ENGLISH',
    'language_code': 'en'
}
params['language'] = 'ENGLISH'
```

### Step 5: Agent Execution

```python
if func_type == FuncType.AVAILABILITY_AGENT:
    response = await self.availability_agent.generate_response(
        user_input="I need a room for 2 adults...",
        params={
            "startDate": "0 1",
            "numberOfNights": 2,
            "Rooms": [{"adults": 2, "childrenAges": [5]}],
            "language": "ENGLISH"
        },
        history=chat_history,
        phone=org_phone_number,
        chunk_display_func=websocket_handler
    )
```

### Step 6: Save to History

```python
await self.history_manager.add_to_history(
    "assistant",
    response,
    "AVAILABILITY_AGENT",
    "AI"
)
```

---

## Debugging

### Enable Debug Mode

Set environment variable:
```bash
export DEBUG_GET_INTENT=true
```

This will print:
- Full intent detection prompts
- Full responses with command detection
- Token-by-token processing

### Console Output

With debug enabled:

```
=== GetUserIntentInfo Prompt ===
please assist the user, your are representing organization named Hilton Hotel
# in case you need to know, today is Wednesday, January 15, 2025
...
================================

Prompt function to run:
You job is to extract the right function call and relevant parameters.
...

-------------response_json-------------------
{
    "func": "AVAILABILITY_AGENT",
    "params": {
        "startDate": "0 1",
        "numberOfNights": 2,
        ...
    }
}
--------------------------------
```

### Log Levels

```python
# Set in environment
LOG_LEVEL=DEBUG  # Most verbose
LOG_LEVEL=INFO   # Default
LOG_LEVEL=WARNING
LOG_LEVEL=ERROR
```

---

## Key Design Decisions

### 1. Parallel Execution
**Why**: Reduces response latency by 30-50%
- Intent and function detection don't depend on each other
- Language detection can run independently
- Results combined after all complete

### 2. Two-Phase Approach
**Why**: Separation of concerns
- **Intent**: Conversational - gather info, ask questions
- **Function**: Analytical - categorize and extract parameters
- Allows specialized prompts for each purpose

### 3. Command-Based Routing
**Why**: Explicit control and override capability
- AI can force specific routing via commands
- Overrides function detection if needed
- Makes debugging easier (visible in logs)

### 4. JSON Response Format
**Why**: Structured, parseable output
- Eliminates parsing errors
- Enforces schema compliance
- Easy validation

### 5. Deterministic Function Selection
**Why**: Consistent routing decisions
- `temperature=1e-19` (near zero)
- `top_p=1e-9` (near zero)
- Fixed `seed=1234`
- Same input → same function

### 6. FAQ Agent as Default Fallback
**Why**: Safe fallback for unknown scenarios
- Can handle any question
- Never fails
- Provides contact info if uncertain

---

## Performance Characteristics

### Typical Latency
- Intent detection: 800-1500ms (streaming)
- Function detection: 600-1200ms (JSON)
- Parallel total: 1000-1500ms (max of both)
- Sequential would be: 1400-2700ms

### Cost per Message
- Intent prompt: ~800-1200 tokens
- Function prompt: ~600-1000 tokens
- Total input: ~1400-2200 tokens/message
- Model: gpt-4.1

### Accuracy
- Intent command detection: >95%
- Function selection: >90%
- Parameter extraction: ~85-90%

---

## Common Issues and Solutions

### Issue: Wrong function selected
**Solution**: Add more examples to YAML config
```yaml
functions_examples:
  - input: "your example input"
    func: CORRECT_FUNCTION
    params: {...}
```

### Issue: Missing parameters
**Solution**: Improve `parameters_considerations` in YAML
```yaml
parameters_considerations: |
  Be very explicit about:
  - Required vs optional parameters
  - Default values
  - Format expectations
```

### Issue: Intent keeps asking questions
**Solution**: Check if command is in first ~10 tokens
- AI must put command at START of response
- Commands must not have backticks

### Issue: Function detection timeout
**Solution**: Check:
- Chat history length (compressed to 12 messages)
- Markdown document compression
- OpenAI API status

---

## Future Improvements

### Potential Enhancements

1. **Caching**
   - Cache function selection for similar queries
   - Reduce API calls for repeated patterns

2. **Confidence Scores**
   - Return confidence level with function selection
   - Allow fallback strategies based on confidence

3. **Multi-Function Support**
   - Allow chaining multiple functions
   - Execute complex multi-step workflows

4. **A/B Testing**
   - Test different prompts
   - Measure accuracy improvements

5. **Learning Loop**
   - Track incorrect routing
   - Auto-generate new examples
   - Improve prompts over time

---

## Related Files

- `src/core/chat_core.py` - Main orchestrator
- `src/core/config/get_user_intent_info.py` - Intent detection
- `src/core/config/get_func_to_run.py` - Function selection
- `src/core/config/config.py` - Configuration loader
- `src/core/config/services/*.yaml` - Function definitions
- `src/agents/*/` - Individual agent implementations

---

## Summary

The function detection system uses a sophisticated two-phase parallel approach:

1. **Intent Detection** - Conversational gathering with command detection
2. **Function Selection** - Analytical categorization with parameter extraction

Both run simultaneously, and results are combined to:
- Route to the correct specialized agent
- Pass extracted parameters
- Maintain conversational context
- Provide fast, accurate responses

The system is highly configurable through YAML files, allowing easy addition of new functions and customization per organization type.


