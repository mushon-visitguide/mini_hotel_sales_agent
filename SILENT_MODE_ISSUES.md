# Silent Mode Issues Report

## Summary
The interactive CLI's silent mode (`-s` flag) is designed to show ONLY bot responses with no logs or debug output. However, there are **unconditional print statements** in several files that bypass the `debug` flag and will appear even in silent mode.

## Issues Found

### 🔴 CRITICAL: Unconditional Print Statements

#### 1. **agent/llm/responder.py** (Lines 63-70)
**Problem:** Response generator ALWAYS prints the full prompt in blue
```python
# Print the entire prompt in blue
print("\033[94m" + "=" * 70)
print("[RESPONSE GENERATOR PROMPT]")
print("=" * 70)
print("\n### SYSTEM PROMPT:")
print(system_prompt)
print("\n### USER PROMPT:")
print(prompt)
print("=" * 70 + "\033[0m")
```

**Impact:** Every response generation will print a large blue block with the full system and user prompts. This is the MOST VISIBLE issue.

**Fix:** Add a `debug` parameter to `generate_response()` and wrap these prints:
```python
async def generate_response(
    self,
    user_message: str,
    recent_messages: List[Message],
    current_tool_results: List[ToolExecutionSummary],
    planner_action: str,
    missing_required_parameters: Optional[Dict[str, str]] = None,
    host_guidance_prompt: Optional[str] = None,
    debug: bool = False  # ADD THIS
) -> str:
    # ...

    # Only print in debug mode
    if debug:
        print("\033[94m" + "=" * 70)
        print("[RESPONSE GENERATOR PROMPT]")
        print("=" * 70)
        print("\n### SYSTEM PROMPT:")
        print(system_prompt)
        print("\n### USER PROMPT:")
        print(prompt)
        print("=" * 70 + "\033[0m")
```

**Files to update:**
- `/home/mushon/hotel_sales_ai_agent/agent/llm/responder.py:23` - Add `debug` parameter
- `/home/mushon/hotel_sales_ai_agent/agent/llm/responder.py:63-70` - Wrap prints in `if debug:`
- `/home/mushon/hotel_sales_ai_agent/agent/core/orchestrator.py:539` - Pass `debug=debug` to `generate_response()`

---

#### 2. **cli_interactive.py** (Lines 159, 175, 198, 216)
**Problem:** Error and goodbye messages ignore silent mode
```python
# Line 159 - in process_in_background exception handler
print(f"\n{Colors.RED}❌ Error: {e}{Colors.END}\n")

# Line 175 - in quit handler
print(f"\n{Colors.YELLOW}Goodbye! 👋{Colors.END}")

# Line 198 - in KeyboardInterrupt handler
print(f"\n{Colors.YELLOW}Goodbye! 👋{Colors.END}")

# Line 216 - in main KeyboardInterrupt handler
print(f"\n{Colors.YELLOW}Goodbye! 👋{Colors.END}")
```

**Impact:** Errors and "Goodbye" messages will show in silent mode

**Fix:** Wrap in `if not silent_mode:` checks

**Files to update:**
- `/home/mushon/hotel_sales_ai_agent/cli_interactive.py:159` - Check silent mode before error print
- `/home/mushon/hotel_sales_ai_agent/cli_interactive.py:175,198,216` - Check silent mode before goodbye

---

### 🟡 LOWER PRIORITY: Debug-Gated Prints (Already Protected)

These are already protected by `if debug:` checks, so they won't appear in silent mode:
- All `[Orchestrator]` prints in orchestrator.py (lines 150-554)
- All `[Runtime]` prints in runtime.py (lines 69-534)
- All `[SessionManager]` prints in session_manager.py (lines 142-259)
- All progress/processing prints in cli_interactive.py (lines 94-156)

**Status:** ✅ These are fine - no changes needed

---

### 🟢 LOGGER STATEMENTS (Already Suppressed)

The logging configuration in cli_interactive.py properly suppresses logs in silent mode:
```python
if silent_mode:
    logging.basicConfig(level=logging.CRITICAL)
    for logger_name in ['agent', 'src', 'httpx', 'httpcore']:
        logging.getLogger(logger_name).setLevel(logging.CRITICAL)
```

All logger statements (INFO, DEBUG, WARNING, ERROR) are already suppressed.

**Status:** ✅ No issues

---

### 🟢 EXTERNAL LIBRARY LOGS (httpx, openai)

The OpenAI/httpx libraries are also suppressed by the logging configuration.

**Status:** ✅ No issues

---

## Required Fixes

### Fix #1: agent/llm/responder.py

**File:** `/home/mushon/hotel_sales_ai_agent/agent/llm/responder.py`

**Lines 23-31:** Add `debug` parameter
```python
async def generate_response(
    self,
    user_message: str,
    recent_messages: List[Message],
    current_tool_results: List[ToolExecutionSummary],
    planner_action: str,
    missing_required_parameters: Optional[Dict[str, str]] = None,
    host_guidance_prompt: Optional[str] = None,
    debug: bool = False  # ADD THIS
) -> str:
```

**Lines 62-71:** Wrap print statements
```python
# Only print in debug mode
if debug:
    print("\033[94m" + "=" * 70)
    print("[RESPONSE GENERATOR PROMPT]")
    print("=" * 70)
    print("\n### SYSTEM PROMPT:")
    print(system_prompt)
    print("\n### USER PROMPT:")
    print(prompt)
    print("=" * 70 + "\033[0m")
```

---

### Fix #2: agent/core/orchestrator.py

**File:** `/home/mushon/hotel_sales_ai_agent/agent/core/orchestrator.py`

**Line 539:** Pass debug flag to responder
```python
response = await responder.generate_response(
    user_message=message,
    recent_messages=context_manager.get_recent_messages(5),
    current_tool_results=current_tool_results,
    planner_action=planning_result.action,
    missing_required_parameters=planning_result.missing_required_parameters,
    host_guidance_prompt=context_manager.state.metadata.host_guidance_prompt,
    debug=debug  # ADD THIS
)
```

---

### Fix #3: cli_interactive.py

**File:** `/home/mushon/hotel_sales_ai_agent/cli_interactive.py`

**Line 159:** Check silent mode for errors
```python
except Exception as e:
    if not silent_mode:  # ADD THIS CHECK
        print(f"\n{Colors.RED}❌ Error: {e}{Colors.END}\n")
```

**Lines 175, 198, 216:** Check silent mode for goodbye messages
```python
# Line 175 - quit handler
if message.lower() in ['quit', 'exit', 'q']:
    if not silent_mode:  # ADD THIS CHECK
        print(f"\n{Colors.YELLOW}Goodbye! 👋{Colors.END}")
    break

# Line 198 - KeyboardInterrupt handler (inside main_interactive)
except KeyboardInterrupt:
    if not silent_mode:  # ADD THIS CHECK
        print(f"\n{Colors.YELLOW}Goodbye! 👋{Colors.END}")

# Line 216 - KeyboardInterrupt handler (at module level)
except KeyboardInterrupt:
    if not silent_mode:  # ADD THIS CHECK
        print(f"\n{Colors.YELLOW}Goodbye! 👋{Colors.END}")
```

**Note:** For lines 198 and 216, you'll need to access the `silent_mode` variable. Consider refactoring to pass it down or use a module-level flag.

---

## Test Command

After applying fixes, verify with:

```bash
# Test 1: Silent mode (should only show bot response)
python3 cli_interactive.py -s

# Test 2: Normal mode (should show all debug output)
python3 cli_interactive.py

# Test 3: Automated test (check for unwanted output)
python3 test_silent_mode.py
```

**Expected output in silent mode:**
```
>> user message
Bot response only
>> quit
```

NO logging, NO progress messages, NO debug output, NO goodbye message.

---

## Summary Table

| File | Line(s) | Issue | Priority | Status |
|------|---------|-------|----------|--------|
| agent/llm/responder.py | 63-70 | Unconditional prompt print | 🔴 CRITICAL | Needs fix |
| agent/llm/responder.py | 23 | Missing debug parameter | 🔴 CRITICAL | Needs fix |
| agent/core/orchestrator.py | 539 | Not passing debug to responder | 🔴 CRITICAL | Needs fix |
| cli_interactive.py | 159 | Error message ignores silent mode | 🟡 MEDIUM | Needs fix |
| cli_interactive.py | 175,198,216 | Goodbye ignores silent mode | 🟡 MEDIUM | Needs fix |
| All logger statements | Various | Logger output | 🟢 OK | Already suppressed |
| Debug-gated prints | Various | Debug prints | 🟢 OK | Already protected |

---

## Priority Order

1. **CRITICAL (Fix first):** agent/llm/responder.py - This prints on EVERY response
2. **CRITICAL (Fix first):** agent/core/orchestrator.py - Pass debug flag
3. **Medium:** cli_interactive.py errors and goodbye messages
