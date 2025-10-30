# Step 3: Session Management with Cancellation

## Goal
Implement session management to track active operations per user and cancel them when new messages arrive.

## Context
- Each user (identified by phone number) can have one active operation at a time
- When new message arrives while processing, need to cancel previous operation
- WhatsApp messages arrive via webhook/API
- Must handle race conditions (multiple messages arriving quickly)
- System uses cancellation tokens from Step 1

## Requirements

### 1. Session Tracking
- Track active operation per `user_id` (phone number)
- Store cancellation token for each active session
- Clean up completed sessions
- Handle concurrent access safely

### 2. Message Handling Strategy
When new message arrives:
1. Check if user has active operation
2. Cancel previous operation if exists
3. Send acknowledgment to user
4. Start new operation with fresh cancellation token
5. Store new session

### 3. Graceful Cancellation
- Use cancellation tokens from Step 1
- Allow current wave to complete (don't interrupt mid-tool)
- Preserve partial results if useful
- Clean up resources properly
- Log cancellation events

## Files to Examine
- `agent/core/orchestrator.py` - Current message processing
- `agent/core/cancellation.py` - Cancellation tokens (from Step 1)
- `src/conversation/context_manager.py` - Existing context management
- `agent/core/events.py` - Hooks for cancellation events

## Deliverables

### 1. Session Manager Class
**Create `agent/core/session_manager.py`:**

```python
class SessionManager:
    """
    Manages active operations per user with cancellation support.

    Ensures only one operation runs per user at a time.
    Cancels previous operation when new message arrives.
    """

    def __init__(self):
        self.active_sessions: Dict[str, ActiveSession] = {}
        self._lock = asyncio.Lock()

    async def process_message(
        self,
        user_id: str,
        message: str,
        orchestrator: Orchestrator,
        send_message: Callable
    ) -> Dict[str, Any]:
        """
        Process message with automatic cancellation of previous operations.

        Args:
            user_id: User identifier (phone number)
            message: User's message
            orchestrator: Orchestrator instance
            send_message: Function to send WhatsApp messages

        Returns:
            Processing results
        """
        async with self._lock:
            # Cancel previous operation if exists
            if user_id in self.active_sessions:
                await self._cancel_session(user_id, send_message)

            # Create new session
            session = await self._create_session(user_id, message)

        try:
            # Process with cancellation support
            result = await orchestrator.process_message(
                message=message,
                user_id=user_id,
                cancel_token=session.cancel_token,
                send_progress=send_message,
                **session.credentials
            )

            return result

        except CancelledException:
            # Operation was cancelled (new message arrived)
            return {"cancelled": True, "message": "Request cancelled"}

        finally:
            # Clean up session
            async with self._lock:
                if user_id in self.active_sessions:
                    del self.active_sessions[user_id]

    async def _cancel_session(self, user_id: str, send_message: Callable):
        """Cancel active session for user"""
        session = self.active_sessions.get(user_id)

        if session:
            session.cancel_token.cancel()

            # Notify user
            await send_message(
                user_id,
                "Got it! Switching to your new request..."
            )

            logger.info(f"Cancelled session for user {user_id}")

    async def _create_session(self, user_id: str, message: str) -> ActiveSession:
        """Create new session with cancellation token"""
        session = ActiveSession(
            user_id=user_id,
            message=message,
            cancel_token=CancellationToken(),
            started_at=time.time()
        )

        self.active_sessions[user_id] = session
        return session


@dataclass
class ActiveSession:
    """Active operation session for a user"""
    user_id: str
    message: str
    cancel_token: CancellationToken
    started_at: float
    credentials: Dict[str, Any] = field(default_factory=dict)
```

### 2. Orchestrator Integration
**Update `agent/core/orchestrator.py`:**

```python
class Orchestrator:
    async def process_message(
        self,
        message: str,
        user_id: str,
        cancel_token: Optional[CancellationToken] = None,
        send_progress: Optional[Callable] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Process message with cancellation support"""

        # Check cancellation before starting
        if cancel_token and cancel_token.is_cancelled:
            raise CancelledException("Operation cancelled before start")

        # Phase 1: Plan
        plan = await self.planner.plan(message)

        # Check cancellation
        if cancel_token and cancel_token.is_cancelled:
            raise CancelledException("Operation cancelled during planning")

        # Phase 2: Execute with cancellation
        results = await self.runtime.execute(
            plan.tools,
            credentials=kwargs,
            cancel_token=cancel_token
        )

        # Check cancellation
        if cancel_token and cancel_token.is_cancelled:
            raise CancelledException("Operation cancelled during execution")

        # Phase 3: Adaptation (if needed)
        if needs_adaptation:
            if cancel_token and cancel_token.is_cancelled:
                raise CancelledException("Operation cancelled before adaptation")

            adapted = await self.planner.adapt(...)

            if cancel_token and cancel_token.is_cancelled:
                raise CancelledException("Operation cancelled during adaptation")

            results.update(
                await self.runtime.execute(adapted.tools, cancel_token=cancel_token)
            )

        # Phase 4: Response
        response = await self.responder.generate(results)
        return response
```

### 3. WhatsApp Webhook Handler
**Create `agent/webhooks/whatsapp_handler.py`:**

```python
from fastapi import FastAPI, Request
from agent.core.session_manager import SessionManager

app = FastAPI()
session_manager = SessionManager()

@app.post("/webhook/whatsapp")
async def handle_whatsapp_message(request: Request):
    """Handle incoming WhatsApp messages"""

    # Parse WhatsApp webhook payload
    data = await request.json()
    user_phone = extract_user_phone(data)
    message_text = extract_message_text(data)

    # Define message sender
    async def send_whatsapp_message(user_id: str, text: str):
        await whatsapp_client.send_message(
            to=user_id,
            body=text
        )

    # Process with session management
    result = await session_manager.process_message(
        user_id=user_phone,
        message=message_text,
        orchestrator=orchestrator,
        send_message=send_whatsapp_message
    )

    return {"success": True}
```

## Implementation Notes

### Race Condition Handling
```python
# Use asyncio.Lock to prevent race conditions
async with self._lock:
    # Only one message per user processed at a time
    # Cancel previous, then start new
```

### Cancellation Flow
```
User sends: "Check Hanukkah"
    → Session A created, token A
    → Wave 1 executing...

User sends: "Actually Passover"
    → Acquire lock
    → Cancel token A (Wave 1 completes, Wave 2 skipped)
    → Send "Switching to new request..."
    → Create Session B, token B
    → Release lock
    → Start processing Passover

Session A: Raises CancelledException, cleans up
Session B: Processes normally
```

### Memory Management
```python
# Always clean up in finally block
finally:
    if user_id in self.active_sessions:
        del self.active_sessions[user_id]
```

## Success Criteria
- Only one operation per user at any time
- Previous operation cancelled when new message arrives
- User receives acknowledgment of cancellation
- No race conditions with concurrent messages
- Memory cleaned up properly (no leaks)
- Graceful handling of CancelledException
- Logged via hooks for monitoring

## Testing Scenarios
1. **Single message** → Process normally
2. **Two rapid messages** → Cancel first, process second
3. **Message during Wave 1** → Complete Wave 1, skip Wave 2, start new
4. **Message during adaptation** → Cancel adaptation, start new
5. **Three rapid messages** → Cancel first two, process third
6. **Message after completion** → No cancellation, queue for next

## Edge Cases to Handle
- User sends message while previous is cancelling
- Operation completes just as cancellation triggered
- Multiple messages arrive within milliseconds
- User goes offline mid-operation
- Cancellation during critical database operation

## Monitoring & Logging
```python
# Emit events for monitoring
await runtime_events.emit(
    'session_cancelled',
    user_id=user_id,
    reason='new_message_received',
    elapsed_time=time.time() - session.started_at
)

await runtime_events.emit(
    'session_started',
    user_id=user_id,
    message=message
)

await runtime_events.emit(
    'session_completed',
    user_id=user_id,
    duration=duration,
    tools_executed=len(results)
)
```

## Integration with Existing Systems
- Use `ContextManager` from `src/conversation/` for conversation state
- Preserve conversation history even when operation cancelled
- Update progress notifier (Step 2) when cancellation happens
- Reset progress message counter on cancellation
