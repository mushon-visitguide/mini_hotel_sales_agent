# Step 4: Intent Detection for Smart Interruption

## Goal
Implement quick intent classification to distinguish between "status check" vs "new request" when user sends message during active operation.

## Context
- User sends: "Check Hanukkah availability" → Agent starts working (10s operation)
- User sends: "Hi, still there?" → Status check, DON'T cancel operation
- User sends: "Actually make it Passover" → New request, DO cancel operation
- Need FAST classification (<500ms) to respond quickly
- Use lightweight LLM call or pattern matching

## Requirements

### 1. Intent Categories
Classify incoming messages into:
- **`status_check`** - User checking if agent is working
  - "hi still there?"
  - "are you working on it?"
  - "hello?"
  - "???"
  - "still processing?"

- **`new_request`** - User changing their mind
  - "actually make it 2 people"
  - "check passover instead"
  - "cancel that"
  - "no wait, I meant..."

- **`clarification`** - User providing more info (might not cancel)
  - "oh and we need wheelchair access"
  - "make sure it has a balcony"
  - This is tricky - might enhance current request

### 2. Classification Strategy
**Option A: Pattern Matching (Fast, <50ms)**
```python
STATUS_CHECK_PATTERNS = [
    r'^(hi|hello|hey)',
    r'still (there|working|processing)',
    r'^\?+$',
    r'you (there|working)',
]

def is_status_check(message: str) -> bool:
    message_lower = message.lower().strip()
    return any(re.match(pattern, message_lower) for pattern in STATUS_CHECK_PATTERNS)
```

**Option B: Quick LLM Call (~200-500ms)**
```python
async def classify_intent(message: str) -> Intent:
    prompt = f"""
    Classify this message:
    "{message}"

    Categories:
    - status_check: User checking if agent is still working
    - new_request: User wants something different
    - clarification: User adding more details

    Reply with just the category name.
    """

    response = await llm.quick_classify(prompt, max_tokens=10)
    return Intent(response.strip())
```

**Option C: Hybrid (Recommended)**
- Try pattern matching first (instant)
- Fall back to LLM for ambiguous cases

### 3. Response Strategy

```python
async def handle_message_during_operation(
    user_id: str,
    message: str,
    active_session: ActiveSession
):
    # Quick classification
    intent = await classify_intent(message)

    if intent == Intent.STATUS_CHECK:
        # Parallel quick response, DON'T cancel
        await send_message(
            user_id,
            "Yes, I'm still working on your request! Give me just a moment... 🔄"
        )
        # Let operation continue

    elif intent == Intent.NEW_REQUEST:
        # Cancel and restart
        active_session.cancel_token.cancel()
        await send_message(
            user_id,
            "Got it! Switching to your new request..."
        )
        # Start new operation

    elif intent == Intent.CLARIFICATION:
        # This is tricky - might need to:
        # Option 1: Add to context and let current operation finish
        # Option 2: Cancel and re-plan with additional context
        # For now: treat as new request to be safe
        active_session.cancel_token.cancel()
        await send_message(
            user_id,
            "I'll include that in my search..."
        )
```

## Files to Examine
- `agent/llm/client.py` - LLM client for classification
- `agent/core/session_manager.py` - Session management (from Step 3)
- `agent/core/orchestrator.py` - Current processing
- `prompts/` - Existing prompts for reference

## Deliverables

### 1. Intent Classifier
**Create `agent/core/intent_classifier.py`:**

```python
from enum import Enum
from typing import Optional
import re

class Intent(Enum):
    STATUS_CHECK = "status_check"
    NEW_REQUEST = "new_request"
    CLARIFICATION = "clarification"
    UNKNOWN = "unknown"


class IntentClassifier:
    """
    Fast intent classification for interruption handling.

    Uses pattern matching for common cases, LLM for ambiguous ones.
    """

    # Pattern matching for instant classification
    STATUS_CHECK_PATTERNS = [
        r'^(hi|hello|hey|yo)[\s\?]*$',
        r'(still|are you) (there|working|processing)',
        r'^\?+$',
        r'(hello|hi).*there',
        r'taking (long|forever)',
    ]

    NEW_REQUEST_KEYWORDS = [
        'actually', 'instead', 'change', 'cancel',
        'no wait', 'make it', 'check.*instead',
    ]

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client

    async def classify(self, message: str, use_llm: bool = True) -> Intent:
        """
        Classify message intent.

        Args:
            message: User's message
            use_llm: Fall back to LLM if pattern matching is uncertain

        Returns:
            Intent classification
        """
        message_lower = message.lower().strip()

        # Try pattern matching first (instant)
        pattern_result = self._classify_by_patterns(message_lower)

        if pattern_result != Intent.UNKNOWN:
            return pattern_result

        # Fall back to LLM for ambiguous cases
        if use_llm and self.llm_client:
            return await self._classify_by_llm(message)

        # Default to new request if uncertain (safer)
        return Intent.NEW_REQUEST

    def _classify_by_patterns(self, message_lower: str) -> Intent:
        """Fast pattern-based classification"""

        # Status checks (hi, hello, still there?)
        for pattern in self.STATUS_CHECK_PATTERNS:
            if re.search(pattern, message_lower):
                return Intent.STATUS_CHECK

        # New requests (actually, instead, change)
        for keyword in self.NEW_REQUEST_KEYWORDS:
            if re.search(keyword, message_lower):
                return Intent.NEW_REQUEST

        # Short messages might be status checks
        if len(message_lower) < 10 and '?' in message_lower:
            return Intent.STATUS_CHECK

        return Intent.UNKNOWN

    async def _classify_by_llm(self, message: str) -> Intent:
        """LLM-based classification for ambiguous cases"""

        prompt = f"""Classify this message into ONE category:

Message: "{message}"

Categories:
- status_check: User is checking if you're still working (e.g., "hi there?", "still processing?")
- new_request: User wants something different (e.g., "actually make it 2 people", "check Passover instead")
- clarification: User is adding details to current request (e.g., "and we need parking")

Reply with ONLY the category name (status_check, new_request, or clarification).
"""

        response = await self.llm_client.quick_completion(
            prompt=prompt,
            max_tokens=20,
            temperature=0
        )

        response_lower = response.strip().lower()

        if "status_check" in response_lower:
            return Intent.STATUS_CHECK
        elif "new_request" in response_lower:
            return Intent.NEW_REQUEST
        elif "clarification" in response_lower:
            return Intent.CLARIFICATION

        # Default to new request if unclear
        return Intent.NEW_REQUEST
```

### 2. Session Manager Integration
**Update `agent/core/session_manager.py`:**

```python
class SessionManager:
    def __init__(self):
        self.active_sessions: Dict[str, ActiveSession] = {}
        self.intent_classifier = IntentClassifier()
        self._lock = asyncio.Lock()

    async def process_message(
        self,
        user_id: str,
        message: str,
        orchestrator: Orchestrator,
        send_message: Callable
    ) -> Dict[str, Any]:
        """Process message with smart intent detection"""

        async with self._lock:
            active_session = self.active_sessions.get(user_id)

            if active_session:
                # Classify intent
                intent = await self.intent_classifier.classify(message)

                if intent == Intent.STATUS_CHECK:
                    # Quick parallel response, don't cancel
                    await send_message(
                        user_id,
                        "Yes! Still working on it, give me just a moment... 🔄"
                    )
                    # Exit without cancelling - operation continues
                    return {"status_check": True, "no_cancellation": True}

                elif intent == Intent.NEW_REQUEST:
                    # Cancel and restart
                    await self._cancel_session(user_id, send_message)
                    # Continue to create new session below

                elif intent == Intent.CLARIFICATION:
                    # For now, treat as new request
                    # TODO: Could enhance current operation with additional context
                    await self._cancel_session(user_id, send_message)

            # Create new session and process
            session = await self._create_session(user_id, message)

        # ... rest of processing ...
```

### 3. Configuration
**Add to settings:**

```python
# Intent classification settings
INTENT_CLASSIFICATION_ENABLED = True
INTENT_USE_LLM_FALLBACK = True  # Use LLM for ambiguous cases
INTENT_CLASSIFICATION_TIMEOUT_MS = 500  # Max time for classification

# Status check auto-responses
STATUS_CHECK_RESPONSES = [
    "Yes! Still working on it, give me just a moment... 🔄",
    "Still here! Processing your request... ⏳",
    "Yes, I'm working on your request! Almost done... ✨",
]
```

## Implementation Notes

### Performance Optimization
```python
# Pattern matching: ~1-5ms
# LLM classification: ~200-500ms

# Use timeout for LLM
try:
    intent = await asyncio.wait_for(
        classifier.classify(message),
        timeout=0.5  # 500ms max
    )
except asyncio.TimeoutError:
    # Default to new_request if LLM is slow
    intent = Intent.NEW_REQUEST
```

### Edge Cases
```python
# User: "hi" (status check)
# Response: "Still working..."
# Operation continues

# User: "hi actually change to 2 people" (new request in greeting)
# Pattern: Contains "actually" and "change"
# Result: NEW_REQUEST
# Action: Cancel and restart

# User: "and we need parking" (clarification)
# This is tricky - could be:
# Option 1: Treat as new request (cancel and re-plan)
# Option 2: Add to context (continue current operation)
# For safety: Treat as new request
```

## Success Criteria
- Status checks respond quickly (<1s) without cancelling
- New requests properly cancel and restart
- Pattern matching handles 80%+ of cases (no LLM needed)
- LLM fallback handles ambiguous cases
- Total classification time < 500ms
- No false positives (status check misclassified as new request)

## Testing Scenarios
1. **"hi still there?"** → Status check, quick response, no cancel
2. **"actually 2 people"** → New request, cancel + restart
3. **"check passover instead"** → New request, cancel + restart
4. **"???"** → Status check (pattern: only question marks)
5. **"and make sure it has wifi"** → Clarification (treat as new request for safety)
6. **"hello can you check if rooms have balconies"** → New request (contains action)

## Monitoring & Metrics
```python
# Track classification accuracy
await runtime_events.emit(
    'intent_classified',
    user_id=user_id,
    message=message,
    intent=intent,
    method='pattern' | 'llm',
    classification_time_ms=duration
)

# Track false positives/negatives
# Manual review: Did we cancel when we shouldn't have?
# Manual review: Did we NOT cancel when we should have?
```

## Future Enhancements
1. **Learn from corrections** - User says "no I meant status check", learn pattern
2. **Context-aware** - Consider conversation history
3. **Multi-language** - Support Hebrew, Arabic, etc.
4. **Confidence scores** - "80% sure this is status check"
