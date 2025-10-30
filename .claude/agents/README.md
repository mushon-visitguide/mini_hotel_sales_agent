# Agent Implementation Steps - WhatsApp Hotel Bot

This directory contains agent definitions for implementing the feedback loop and cancellation system for the hotel booking AI agent.

## Overview

The goal is to make the system **responsive, adaptive, and production-ready for WhatsApp** by adding:
1. Cancellation when users send new messages
2. Progress updates to keep users informed
3. Smart intent detection (status check vs new request)
4. Feedback loop for handling edge cases (no availability, errors)

## Implementation Order

### Step 1: Cancellation Token System ⭐ START HERE
**File:** `step1-cancellation-token.md`

**Goal:** Allow graceful cancellation of ongoing operations

**What it does:**
- Creates `CancellationToken` class (simple flag)
- Integrates with Runtime to check cancellation before each wave
- Raises `CancelledException` when cancelled
- Foundation for Steps 2-5

**Time:** 1 day
**Priority:** 🔴 Critical (everything else depends on this)

---

### Step 2: Progress Notifications
**File:** `step2-progress-notifications.md`

**Goal:** Send WhatsApp updates during long operations

**What it does:**
- Smart throttling (max 2 messages per request)
- Sends update if operation > 4 seconds
- Tool-specific messages ("🗓️ Checking dates...", "🔍 Searching rooms...")
- Integrated with hooks system

**Time:** 0.5 day
**Priority:** 🟡 High (better UX, but not blocking)

---

### Step 3: Session Management
**File:** `step3-session-management.md`

**Goal:** Track active operations per user, cancel on new message

**What it does:**
- `SessionManager` tracks one operation per user_id
- Cancels previous operation when new message arrives
- Handles race conditions with async locks
- Integrates with WhatsApp webhook

**Time:** 0.5 day
**Priority:** 🔴 Critical (core WhatsApp behavior)

**Depends on:** Step 1 (cancellation tokens)

---

### Step 4: Intent Detection
**File:** `step4-intent-detection.md`

**Goal:** Distinguish "status check" from "new request"

**What it does:**
- Pattern matching for common phrases ("hi still there?")
- LLM fallback for ambiguous cases
- Status checks get quick response without cancelling
- New requests cancel previous operation

**Time:** 1 day
**Priority:** 🟡 Medium (nice to have, improves UX)

**Depends on:** Step 3 (session management)

---

### Step 5: Feedback Loop with Validation
**File:** `step5-feedback-loop.md`

**Goal:** Adapt strategy when results are insufficient

**What it does:**
- `ResultValidator` checks if results are usable
- Automatically tries alternatives (no availability → nearby dates)
- Max 1 adaptation turn (prevents infinite loops)
- Integrates with cancellation system

**Time:** 2 days
**Priority:** 🔴 Critical (handles edge cases, production readiness)

**Depends on:** Step 1 (cancellation), Step 3 (session management)

---

## Quick Start

### Minimal Implementation (Week 1)
Implement these for basic functionality:
1. ✅ Step 1: Cancellation Token (1 day)
2. ✅ Step 3: Session Management (0.5 day)
3. ✅ Step 2: Progress Notifications (0.5 day)

**Result:** Responsive bot that cancels on new messages and shows progress

---

### Full Implementation (Week 2)
Add these for production-ready system:
4. ✅ Step 4: Intent Detection (1 day)
5. ✅ Step 5: Feedback Loop (2 days)

**Result:** Professional bot that handles all edge cases

---

## Architecture Overview

```
User sends: "Check Hanukkah availability"
    ↓
SessionManager: Create session with CancellationToken
    ↓
ProgressNotifier: "⏳ Checking dates..."
    ↓
Orchestrator: Execute initial plan
    - calendar → "8 nights Dec 14-22"
    - availability(8 nights) → [] empty
    ↓
Validator: "No availability for 8 nights"
    ↓
Orchestrator: Adapt plan
    - availability(2 nights) → [rooms found]
    ↓
Response: "Full 8 nights unavailable, but weekend available!"

---

[During execution]
User sends: "Actually Passover instead"
    ↓
IntentClassifier: NEW_REQUEST
    ↓
SessionManager: Cancel Hanukkah operation
    ↓
ProgressNotifier: "Got it! Switching to Passover..."
    ↓
Start new session for Passover
```

---

## File Structure After Implementation

```
agent/
  core/
    cancellation.py          # Step 1: CancellationToken, CancelledException
    progress_notifier.py     # Step 2: SmartProgressNotifier
    session_manager.py       # Step 3: SessionManager
    intent_classifier.py     # Step 4: IntentClassifier
    validator.py            # Step 5: ResultValidator
    orchestrator.py         # Updated with feedback loop
    runtime.py              # Updated with cancellation checks

  webhooks/
    whatsapp_handler.py     # WhatsApp webhook integration
```

---

## Success Metrics

### Before Implementation
- ❌ Operations can't be cancelled
- ❌ Users wait in silence (feels broken)
- ❌ Can't recover from "no availability"
- ❌ New messages while processing = confusion

### After Implementation
- ✅ Instant cancellation on new message
- ✅ Progress updates every 3-4 seconds
- ✅ Smart detection: "hi" vs "check passover instead"
- ✅ Adapts when no availability (tries alternatives)
- ✅ Production-ready for WhatsApp

---

## Testing Checklist

- [ ] Cancel operation mid-execution
- [ ] Send "hi still there?" → quick response, no cancel
- [ ] Send "actually 2 people" → cancel + restart
- [ ] Long operation → receives progress updates
- [ ] No availability → tries nearby dates
- [ ] Rapid messages → handles race conditions
- [ ] Operation completes before cancellation → graceful
- [ ] Max adaptation turns → doesn't loop forever

---

## Next Steps

1. **Read** `step1-cancellation-token.md`
2. **Implement** cancellation system
3. **Test** basic cancellation
4. **Move to** Step 2 or Step 3
5. **Iterate** through all steps

---

## Questions?

Each agent file contains:
- Goal and context
- Detailed requirements
- Code examples
- Implementation notes
- Success criteria
- Testing scenarios

Start with Step 1 and work sequentially!
