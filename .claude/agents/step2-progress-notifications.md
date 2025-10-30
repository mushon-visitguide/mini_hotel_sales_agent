# Step 2: Progress Notification System

## Goal
Implement smart progress notifications for WhatsApp to keep users informed during long operations (3-20 seconds).

## Context
- Users expect response within 3-4 seconds on WhatsApp
- Operations can take 10-20 seconds (calendar ~6s, availability ~3-5s, adaptation adds more)
- Each progress message triggers a WhatsApp notification
- **CRITICAL:** Max 1-2 progress messages total (avoid spam)
- Calendar tool is consistently slowest
- Existing `agent/core/progress_notifier.py` provides basic structure

## Requirements

### 1. Smart Throttling
- Send progress message ONLY if operation will take > 4 seconds
- Max 2 progress messages per request:
  - **First:** When slow tool detected or 4s elapsed
  - **Second:** If operation exceeds 10s total
- Use hooks system to detect tool execution timing

### 2. Tool-Specific Detection
Prioritize messages based on known slow tools:
- **calendar.resolve_date_hint** (~6s) → Always send progress
- **pms.get_availability_and_pricing** (~3-5s) → Send if no calendar
- **Adaptation phase** → Send "Finding alternatives..."

### 3. Progress Messages
Keep messages short and informative:
- **Initial:** "⏳ Checking dates..." (when calendar starts)
- **Initial:** "🔍 Searching for rooms..." (when availability starts, no calendar)
- **Mid-way:** "🔄 Still working, almost done..." (if >10s total)
- **Adaptation:** "🔄 Trying alternatives..." (when adaptation starts)

### 4. Integration Points
- Use existing `agent/core/events.py` hooks system
- Listen to `tool_start`, `wave_start` events
- Track elapsed time since request started
- Integrate with WhatsApp Cloud API for sending

## Files to Examine
- `agent/core/progress_notifier.py` - Existing basic implementation
- `agent/core/events.py` - Hooks system with tool/wave events
- `agent/core/runtime.py` - Wave execution with timing
- `agent/core/orchestrator.py` - Overall request handling

## Deliverables

1. **Enhanced agent/core/progress_notifier.py**
   ```python
   class SmartProgressNotifier:
       MAX_MESSAGES = 2  # Hard limit
       SLOW_TOOL_THRESHOLD = 4  # seconds
       LONG_OPERATION_THRESHOLD = 10  # seconds

       def __init__(self, send_message_func):
           self.messages_sent = 0
           self.start_time = None
           self.send_message = send_message_func

       async def on_tool_start(self, tool_name, **kwargs):
           # Send progress if slow tool and under message limit
           if self._is_slow_tool(tool_name) and self.messages_sent < 1:
               await self._send_progress(self._get_tool_message(tool_name))

       async def check_elapsed_time(self):
           # Send mid-way update if operation is taking long
           if self.elapsed > 10 and self.messages_sent < 2:
               await self._send_progress("🔄 Still working, almost done...")
   ```

2. **WhatsApp Integration Helper**
   ```python
   class WhatsAppProgressNotifier(SmartProgressNotifier):
       def __init__(self, whatsapp_client, user_phone):
           async def send_via_whatsapp(msg):
               await whatsapp_client.send_message(user_phone, msg)

           super().__init__(send_message=send_via_whatsapp)
   ```

3. **Orchestrator Integration**
   - Create progress notifier at start of request
   - Pass to runtime/planner for progress updates
   - Track timing across entire request lifecycle

4. **Configuration**
   - Enable/disable progress notifications
   - Configure thresholds (slow tool, long operation)
   - Configure message templates

## Implementation Notes

### Timing Strategy
```python
# Request starts
start_time = time.time()

# Wave 1: calendar tool starts
if tool == "calendar.resolve_date_hint":
    send("⏳ Checking dates...")  # Message 1/2
    messages_sent = 1

# 10 seconds elapsed
if time.time() - start_time > 10 and messages_sent < 2:
    send("🔄 Still working...")  # Message 2/2
    messages_sent = 2

# No more messages allowed (messages_sent = 2)
```

### Slow Tool Detection
```python
SLOW_TOOLS = {
    'calendar.resolve_date_hint': '🗓️ Checking dates...',
    'pms.get_availability_and_pricing': '🔍 Searching for rooms...',
}

def should_send_progress(tool_name):
    return (
        tool_name in SLOW_TOOLS and
        messages_sent < MAX_MESSAGES
    )
```

## Success Criteria
- Users receive feedback within 4 seconds if operation is slow
- Max 2 progress messages per request (never more)
- Messages are contextual and helpful
- No messages for fast operations (<4s total)
- Clean integration with WhatsApp Cloud API
- Respects message limits even with multiple adaptations

## Testing Scenarios
1. **Fast operation** (<4s) → No progress messages
2. **Calendar only** (~6s) → 1 message: "Checking dates..."
3. **Long operation** (15s) → 2 messages: Initial + "Still working..."
4. **With adaptation** → Messages: Initial + "Trying alternatives..."
5. **Rapid completion** → Don't send second message if first wave finishes quickly

## WhatsApp Cloud API Integration
```python
# Example usage with WhatsApp
from whatsapp_cloud_api import WhatsApp

whatsapp = WhatsApp(token=TOKEN, phone_number_id=PHONE_ID)

notifier = WhatsAppProgressNotifier(
    whatsapp_client=whatsapp,
    user_phone="+1234567890"
)

# Setup hooks
notifier.setup()

# Now progress updates automatically sent via WhatsApp
```

## Edge Cases to Handle
- User sends new message mid-operation (cancel + reset counter)
- Operation completes before progress message sent (skip message)
- Multiple slow tools in same wave (send only once)
- Adaptation happens quickly (don't send "trying alternatives" if <2s)
