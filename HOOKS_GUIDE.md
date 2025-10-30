# Hooks System Guide

## Overview

The hooks system provides an **event-driven architecture** for monitoring, logging, and extending tool execution without modifying core code.

Think of hooks like electrical outlets - the system provides "sockets" at key points, and you can "plug in" whatever functionality you need.

---

## Quick Start

### 1. Basic Usage (Already Setup)

The system is **already configured** in `main.py`:

```python
from agent.core.hooks import setup_all_hooks, MetricsHooks

# Setup at startup (already done in main.py)
setup_all_hooks(verbose=False, enable_performance_monitoring=True)

# During runtime
python main.py

# View metrics
> metrics
```

### 2. Enable Verbose Logging

```bash
# Set environment variable
export VERBOSE_LOGGING=true
python main.py
```

---

## Available Events

The system emits these events during tool execution:

### Tool Events

**`tool_start`** - Fires when a tool begins execution
- `tool_id`: Unique identifier for this tool call
- `tool_name`: Name of the tool (e.g., "pms.get_availability")
- `args`: Tool arguments (credentials redacted)

**`tool_complete`** - Fires when a tool succeeds
- `tool_id`: Unique identifier
- `tool_name`: Name of the tool
- `duration_ms`: Time taken in milliseconds
- `success`: Always `True`

**`tool_error`** - Fires when a tool fails
- `tool_id`: Unique identifier
- `tool_name`: Name of the tool
- `error`: Error message
- `duration_ms`: Time before failure
- `error_type`: Type of error (`"timeout"` or `"execution_error"`)

### Wave Events

**`wave_start`** - Fires when a wave begins execution
- `wave_num`: Current wave number (1-indexed)
- `total_waves`: Total number of waves
- `tools`: List of tools in this wave

**`wave_complete`** - Fires when a wave completes
- `wave_num`: Wave number
- `total_waves`: Total waves
- `duration_ms`: Total wave duration
- `tool_count`: Number of tools in wave

---

## Pre-built Hook Sets

### 1. Standard Logging (Default)

```python
from agent.core.hooks import LoggingHooks

# Setup standard logging
LoggingHooks.setup(verbose=False)
```

**Output:**
```
🔧 Starting: calendar.resolve_date_hint
✅ Completed: calendar.resolve_date_hint (234ms)
🌊 Wave 1/2: 2 tools → ['calendar.resolve_date_hint', 'faq.get_rooms_info']
✅ Wave 1/2 completed (450ms)
```

### 2. Verbose Logging

```python
LoggingHooks.setup(verbose=True)
```

**Output:**
```
🔧 [Tool Start] resolve_dates: calendar.resolve_date_hint
   Args: {'date_hint': 'tomorrow', 'current_date': '2025-10-30'}
✅ [Tool Complete] resolve_dates: calendar.resolve_date_hint (234ms)
```

### 3. Metrics Tracking

```python
from agent.core.hooks import MetricsHooks

# Setup metrics
MetricsHooks.setup()

# View stats anytime
MetricsHooks.print_stats()
# Or get specific tool
MetricsHooks.print_stats('pms.get_availability')
```

**Output:**
```
📊 Overall Metrics:
  Total executions: 25
  Total errors: 2
  Success rate: 92.0%
  Avg duration: 1234ms
  Tools used: calendar.resolve_date_hint, pms.get_availability, faq.get_rooms_info
```

### 4. Performance Monitoring

```python
from agent.core.hooks import PerformanceHooks

# Warn if tool > 5s or wave > 10s
perf = PerformanceHooks(slow_tool_threshold_ms=5000, slow_wave_threshold_ms=10000)
perf.setup()
```

**Output:**
```
⚠️ Slow tool detected: pms.get_availability took 6234ms (threshold: 5000ms)
```

### 5. Debug Mode

```python
from agent.core.hooks import DebugHooks

# Very verbose - every detail
DebugHooks.setup()
```

---

## Custom Hooks

Create your own hooks for specific needs:

### Example 1: Slack Notifications

```python
from agent.core.events import runtime_events

async def notify_slack_on_error(tool_name, error, **kwargs):
    """Send Slack alert when tool fails"""
    if tool_name == "pms.create_booking":
        slack_client.send_message(
            channel="#alerts",
            text=f"🚨 Booking creation failed: {error}"
        )

# Register hook
runtime_events.on('tool_error', notify_slack_on_error)
```

### Example 2: Database Audit Log

```python
async def audit_log_tool_execution(tool_name, duration_ms, **kwargs):
    """Record all tool executions to database"""
    await db.execute("""
        INSERT INTO tool_audit_log (tool_name, duration_ms, timestamp)
        VALUES (?, ?, NOW())
    """, tool_name, duration_ms)

runtime_events.on('tool_complete', audit_log_tool_execution)
```

### Example 3: Cost Tracking

```python
PMS_API_COSTS = {
    "pms.get_availability": 0.01,  # $0.01 per call
    "pms.create_booking": 0.05,    # $0.05 per call
}

async def track_api_costs(tool_name, **kwargs):
    """Track API usage costs"""
    cost = PMS_API_COSTS.get(tool_name, 0)
    if cost > 0:
        await billing.record_charge(hotel_id, cost, f"API call: {tool_name}")

runtime_events.on('tool_complete', track_api_costs)
```

### Example 4: Real-time User Notifications

```python
async def notify_user_progress(tool_name, **kwargs):
    """Show user what's happening in real-time"""
    messages = {
        "calendar.resolve_date_hint": "🗓️ Checking dates...",
        "pms.get_availability": "🔍 Searching for available rooms...",
        "pms.create_booking": "✨ Creating your reservation..."
    }

    message = messages.get(tool_name, f"⚙️ {tool_name}...")
    await websocket.send_to_user(message)

runtime_events.on('tool_start', notify_user_progress)
```

### Example 5: Retry Failed Tools

```python
async def auto_retry_availability(tool_id, tool_name, error, **kwargs):
    """Retry availability check if it fails"""
    if tool_name == "pms.get_availability" and "timeout" in error.lower():
        logger.info(f"Retrying {tool_name} after timeout...")
        # Trigger retry with longer timeout
        await registry.call(tool_name, timeout=60, ...)

runtime_events.on('tool_error', auto_retry_availability)
```

---

## Hook API Reference

### EventEmitter

```python
from agent.core.events import runtime_events

# Register listener
runtime_events.on('event_name', callback_function)

# Remove listener
runtime_events.off('event_name', callback_function)

# Register one-time listener
runtime_events.once('event_name', callback_function)

# Emit event (internal use)
await runtime_events.emit('event_name', param1=value1, param2=value2)

# Remove all listeners
runtime_events.remove_all_listeners('event_name')
# Or all events
runtime_events.remove_all_listeners()
```

### Callback Signature

Callbacks receive event-specific keyword arguments:

```python
# Sync callback
def my_hook(tool_name, duration_ms, **kwargs):
    print(f"{tool_name} took {duration_ms}ms")

# Async callback (recommended)
async def my_async_hook(tool_name, duration_ms, **kwargs):
    await db.log(tool_name, duration_ms)

runtime_events.on('tool_complete', my_hook)
runtime_events.on('tool_complete', my_async_hook)
```

---

## Environment Variables

Control hook behavior via environment variables:

```bash
# Enable verbose logging
export VERBOSE_LOGGING=true

# Disable performance monitoring
# (Modify setup_all_hooks call in main.py)
```

---

## CLI Commands

Interactive commands in `main.py`:

- `metrics` - Show tool performance statistics
- `status` - Show booking context
- `reset` - Start new session (resets metrics)
- `quit` / `exit` - Exit program

---

## Best Practices

### 1. Keep Hooks Lightweight
```python
# ✅ Good - fast operation
async def log_tool(tool_name, **kwargs):
    logger.info(f"Tool: {tool_name}")

# ❌ Bad - slow operation blocks execution
async def slow_hook(tool_name, **kwargs):
    await expensive_api_call()  # This slows down every tool!
```

### 2. Handle Errors in Hooks
```python
# ✅ Good - errors are caught
async def safe_hook(tool_name, **kwargs):
    try:
        await risky_operation()
    except Exception as e:
        logger.error(f"Hook failed: {e}")

# ❌ Bad - error breaks tool execution
async def unsafe_hook(tool_name, **kwargs):
    await risky_operation()  # If this fails, tool execution stops!
```

### 3. Use **kwargs for Future Compatibility
```python
# ✅ Good - handles new fields
async def flexible_hook(tool_name, duration_ms, **kwargs):
    # Works even if new fields are added
    pass

# ❌ Bad - breaks if new fields added
async def rigid_hook(tool_name, duration_ms):
    # Will break when new event fields are added
    pass
```

---

## Architecture Benefits

### Why Use Hooks?

✅ **Separation of Concerns** - Monitoring code separate from business logic
✅ **Extensibility** - Add features without modifying core code
✅ **Reusability** - Same hook works across different projects
✅ **Testing** - Easy to add test hooks
✅ **Production Ready** - Add metrics, alerts, auditing easily

### What Gemini CLI Does

Gemini CLI uses the same pattern:

```typescript
// gemini-cli/packages/core/src/utils/events.ts
coreEvents.on('tool-execution-start', (toolName) => {
  telemetry.recordToolStart(toolName);
});
```

---

## Examples from Real Usage

### Startup (main.py)
```python
# Setup all hooks at startup
setup_all_hooks(verbose=False, enable_performance_monitoring=True)
```

### Runtime (automatic)
```
🔧 Starting: calendar.resolve_date_hint
✅ Completed: calendar.resolve_date_hint (234ms)
🌊 Wave 1/1: 1 tools → ['calendar.resolve_date_hint']
✅ Wave 1/1 completed (234ms)
```

### View Metrics
```
> metrics

📊 TOOL PERFORMANCE METRICS
======================================================================

Overall Statistics:
  Total executions: 5
  Total errors: 0
  Success rate: 100.0%
  Average duration: 1456ms

Per-Tool Statistics:

  calendar.resolve_date_hint
    Calls: 2
    Errors: 0
    Success rate: 100.0%
    Avg duration: 234ms
    Min/Max: 220ms / 248ms

  pms.get_availability_and_pricing
    Calls: 2
    Errors: 0
    Success rate: 100.0%
    Avg duration: 2345ms
    Min/Max: 2100ms / 2590ms
```

---

## Summary

The hooks system provides:
- 🪝 **Event-driven architecture** for monitoring and extension
- 📊 **Built-in metrics tracking** with performance stats
- 🔍 **Flexible logging** (standard and verbose modes)
- ⚡ **Performance monitoring** with slow operation warnings
- 🔧 **Easy customization** - create your own hooks
- 🎯 **Production ready** - add monitoring, alerts, auditing

All without modifying core Runtime code!
