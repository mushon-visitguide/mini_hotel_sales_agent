# Step 1: Cancellation Token System

## Goal
Implement a CancellationToken system to allow graceful cancellation of ongoing operations when users send new messages.

## Context
- Agent processes messages that can take 10-20 seconds (calendar tool ~6s, availability checks ~3-5s)
- Users on WhatsApp might send new messages while agent is working
- Need to cancel ongoing operations without leaving things in broken state
- System uses async Python with wave-based parallel tool execution in `agent/core/runtime.py`

## Requirements

### 1. CancellationToken Class
- Create `agent/core/cancellation.py`
- Simple flag-based token that can be checked during execution
- Thread-safe for async operations
- Support checking `is_cancelled` property
- Method to trigger cancellation: `cancel()`

### 2. Runtime Integration
- Update `agent/core/runtime.py`
- Accept optional `cancel_token` parameter in `execute()` method
- Check cancellation before each wave execution
- Raise `CancelledException` if cancelled during execution
- Allow current wave to finish gracefully (don't interrupt mid-tool)

### 3. Orchestrator Integration
- Update `agent/core/orchestrator.py`
- Create cancellation token before starting execution
- Pass token to runtime.execute()
- Catch CancelledException and handle gracefully
- Clean up resources on cancellation

### 4. Error Handling
- Define `CancelledException` exception class
- Handle partial results when cancelled
- Log cancellation events via hooks
- Don't crash on cancellation - return graceful response

## Files to Examine
- `agent/core/runtime.py` - Runtime class with wave execution
- `agent/core/orchestrator.py` - Orchestrator that calls runtime
- `agent/core/events.py` - Hook system for logging cancellation events

## Deliverables

1. **agent/core/cancellation.py**
   ```python
   class CancellationToken:
       """Simple cancellation token for async operations"""
       def __init__(self): ...
       def cancel(self): ...
       def is_cancelled(self) -> bool: ...

   class CancelledException(Exception):
       """Raised when operation is cancelled"""
       pass
   ```

2. **Updated agent/core/runtime.py**
   - Add `cancel_token: Optional[CancellationToken] = None` parameter
   - Check `cancel_token.is_cancelled` before each wave
   - Raise CancelledException if cancelled

3. **Updated agent/core/orchestrator.py**
   - Create cancellation token
   - Pass to runtime.execute()
   - Handle CancelledException with try/catch

4. **Example Usage**
   ```python
   # Create token
   token = CancellationToken()

   # Start operation
   task = asyncio.create_task(orchestrator.process_message(..., token))

   # Cancel from another context (e.g., new message arrives)
   token.cancel()

   # Operation will stop gracefully
   ```

## Implementation Notes
- Keep it simple - just a boolean flag with thread-safe access
- Check cancellation at wave boundaries (not mid-tool) for clean state
- Emit cancellation events via hooks for monitoring
- Return partial results if possible when cancelled

## Success Criteria
- Can cancel ongoing operation from external code
- Cancellation is graceful (no corrupted state)
- Partial results are preserved when applicable
- Proper logging via hooks system
- No memory leaks (tokens are cleaned up)

## Testing Scenarios
1. Cancel during wave 1 execution
2. Cancel between waves
3. Cancel during adaptation phase
4. Multiple rapid cancellations
5. Cancel after completion (should be no-op)
