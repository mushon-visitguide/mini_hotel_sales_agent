"""
Session Management for WhatsApp Hotel Bot

Manages active operations per user with automatic cancellation support.
Ensures only one operation runs per user at a time.
Integrates with intent classification for smart interruption handling.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Callable, Awaitable, TYPE_CHECKING

from agent.core.cancellation import CancellationToken, CancelledException
from agent.core.events import runtime_events
from agent.core.intent_classifier import IntentClassifier, Intent

if TYPE_CHECKING:
    from agent.core.orchestrator import Orchestrator

logger = logging.getLogger(__name__)


@dataclass
class ActiveSession:
    """
    Represents an active operation session for a user.

    Attributes:
        user_id: User identifier (phone number)
        message: User's message being processed
        cancel_token: Cancellation token for this session
        started_at: Timestamp when session started
        credentials: PMS credentials for this session
    """
    user_id: str
    message: str
    cancel_token: CancellationToken
    started_at: float
    credentials: Dict[str, Any] = field(default_factory=dict)

    @property
    def elapsed_time(self) -> float:
        """Get elapsed time since session started"""
        return time.time() - self.started_at


class SessionManager:
    """
    Manages active operations per user with cancellation support.

    Features:
    - One operation per user at a time
    - Smart intent detection (status check vs new request)
    - Cancels previous operation only when needed
    - Thread-safe with async locks
    - Automatic cleanup on completion
    - Integrates with cancellation token system

    Usage:
        session_manager = SessionManager(intent_classifier=classifier)

        # Process message (auto-cancels previous if needed)
        result = await session_manager.process_message(
            user_id="+1234567890",
            message="Check Hanukkah availability",
            orchestrator=orchestrator,
            send_message=send_whatsapp_message,
            pms_credentials={...}
        )
    """

    # Default status check responses (rotated for variety)
    STATUS_CHECK_RESPONSES = [
        "Yes! Still working on it, give me just a moment... 🔄",
        "Still here! Processing your request... ⏳",
        "Yes, I'm working on your request! Almost done... ✨",
    ]

    def __init__(self, intent_classifier: Optional[IntentClassifier] = None):
        """
        Initialize session manager.

        Args:
            intent_classifier: Optional intent classifier for smart interruption
                              If None, always treats new messages as new requests
        """
        self.active_sessions: Dict[str, ActiveSession] = {}
        self._lock = asyncio.Lock()
        self.intent_classifier = intent_classifier or IntentClassifier()
        self._status_response_index = 0  # For rotating responses

        logger.info("SessionManager initialized")
        if intent_classifier:
            logger.info("Intent classification enabled")

    async def process_message(
        self,
        user_id: str,
        message: str,
        orchestrator: "Orchestrator",
        send_message: Callable[[str, str], Awaitable[None]],
        pms_credentials: Dict[str, Any],
        context_manager=None,
        debug: bool = False
    ) -> Dict[str, Any]:
        """
        Process message with automatic cancellation of previous operations.

        Args:
            user_id: User identifier (phone number)
            message: User's message
            orchestrator: Orchestrator instance
            send_message: Function to send messages (user_id, message)
            pms_credentials: PMS credentials dict containing:
                - pms_type
                - pms_username
                - pms_password
                - hotel_id
                - pms_use_sandbox (optional)
                - pms_url_code (optional)
                - pms_agency_channel_id (optional)
            context_manager: Optional conversation context manager
            debug: Enable debug output

        Returns:
            Processing results dictionary

        Raises:
            Exception: If processing fails (cancellation is handled gracefully)
        """
        # Step 1: Check if user has active session and classify intent
        async with self._lock:
            active_session = self.active_sessions.get(user_id)

            if active_session:
                # User has active operation - classify intent
                intent = await self.intent_classifier.classify(message)

                if debug:
                    print(f"[SessionManager] User has active session, intent: {intent.value}")

                # 🪝 Emit intent classified event
                await runtime_events.emit(
                    'intent_classified',
                    user_id=user_id,
                    message=message,
                    intent=intent.value,
                    has_active_session=True
                )

                if intent == Intent.STATUS_CHECK:
                    # Don't cancel - just send quick parallel response
                    response = self._get_status_response()
                    await send_message(user_id, response)

                    if debug:
                        print(f"[SessionManager] Status check detected, not cancelling")

                    # Return immediately without creating new session
                    return {
                        "status_check": True,
                        "no_cancellation": True,
                        "response": response,
                        "active_session_elapsed": active_session.elapsed_time
                    }

                elif intent in (Intent.NEW_REQUEST, Intent.CLARIFICATION):
                    # Cancel and restart
                    if debug:
                        print(f"[SessionManager] {intent.value} detected, cancelling previous operation")

                    await self._cancel_session(user_id, send_message)
                    # Continue to create new session below

                else:  # Intent.UNKNOWN
                    # Default to cancelling for safety
                    logger.debug(f"Intent unknown for '{message}', defaulting to cancellation")
                    await self._cancel_session(user_id, send_message)
                    # Continue to create new session below

            # Step 2: Create new session
            session = self._create_session(user_id, message, pms_credentials)

        if debug:
            print(f"\n[SessionManager] Created new session for {user_id}")
            print(f"[SessionManager] Message: {message}")

        # 🪝 Emit session started event
        await runtime_events.emit(
            'session_started',
            user_id=user_id,
            message=message
        )

        try:
            # Step 3: Process with cancellation support
            result = await orchestrator.process_message(
                message=message,
                pms_type=pms_credentials['pms_type'],
                pms_username=pms_credentials['pms_username'],
                pms_password=pms_credentials['pms_password'],
                hotel_id=pms_credentials['hotel_id'],
                pms_use_sandbox=pms_credentials.get('pms_use_sandbox', False),
                pms_url_code=pms_credentials.get('pms_url_code'),
                pms_agency_channel_id=pms_credentials.get('pms_agency_channel_id'),
                context_manager=context_manager,
                debug=debug,
                cancel_token=session.cancel_token
            )

            # 🪝 Emit session completed event
            await runtime_events.emit(
                'session_completed',
                user_id=user_id,
                duration=session.elapsed_time,
                tools_executed=len(result.get('results', {}))
            )

            return result

        except CancelledException as e:
            # Operation was cancelled (new message arrived)
            logger.info(f"Session cancelled for {user_id}: {e.message}")

            if debug:
                print(f"\n[SessionManager] Session cancelled for {user_id}")
                print(f"[SessionManager] Reason: {e.message}")

            # Return cancellation result (already formatted by orchestrator)
            return {
                "cancelled": True,
                "message": "Request cancelled. Processing your new message...",
                "response": "Request cancelled. Processing your new message...",
                "partial_results": e.partial_results or {}
            }

        except Exception as e:
            # Processing error
            logger.error(f"Session processing error for {user_id}: {e}")

            # 🪝 Emit error event
            await runtime_events.emit(
                'session_error',
                user_id=user_id,
                error=str(e),
                duration=session.elapsed_time
            )

            raise

        finally:
            # Step 4: Clean up session (always runs)
            async with self._lock:
                if user_id in self.active_sessions:
                    del self.active_sessions[user_id]
                    if debug:
                        print(f"[SessionManager] Cleaned up session for {user_id}")

    def _get_status_response(self) -> str:
        """
        Get a status check response (rotates through options for variety).

        Returns:
            Status check response message
        """
        response = self.STATUS_CHECK_RESPONSES[self._status_response_index]
        self._status_response_index = (
            (self._status_response_index + 1) % len(self.STATUS_CHECK_RESPONSES)
        )
        return response

    async def _cancel_session(
        self,
        user_id: str,
        send_message: Callable[[str, str], Awaitable[None]]
    ):
        """
        Cancel active session for user.

        Args:
            user_id: User identifier
            send_message: Function to send cancellation message
        """
        session = self.active_sessions.get(user_id)

        if not session:
            return

        # Cancel the token
        session.cancel_token.cancel(reason="New message received")

        logger.info(
            f"Cancelled session for {user_id} "
            f"(elapsed: {session.elapsed_time:.2f}s, message: '{session.message[:50]}...')"
        )

        # Notify user
        try:
            await send_message(
                user_id,
                "Got it! Switching to your new request..."
            )
        except Exception as e:
            logger.error(f"Failed to send cancellation message to {user_id}: {e}")

        # 🪝 Emit cancellation event
        await runtime_events.emit(
            'session_cancelled',
            user_id=user_id,
            reason='new_message_received',
            elapsed_time=session.elapsed_time,
            cancelled_message=session.message
        )

    def _create_session(
        self,
        user_id: str,
        message: str,
        credentials: Dict[str, Any]
    ) -> ActiveSession:
        """
        Create new session with cancellation token.

        Args:
            user_id: User identifier
            message: User's message
            credentials: PMS credentials

        Returns:
            New ActiveSession instance
        """
        session = ActiveSession(
            user_id=user_id,
            message=message,
            cancel_token=CancellationToken(),
            started_at=time.time(),
            credentials=credentials
        )

        self.active_sessions[user_id] = session

        logger.debug(f"Created session for {user_id}: {message[:50]}...")

        return session

    def get_active_session(self, user_id: str) -> Optional[ActiveSession]:
        """
        Get active session for user if exists.

        Args:
            user_id: User identifier

        Returns:
            ActiveSession if exists, None otherwise
        """
        return self.active_sessions.get(user_id)

    def has_active_session(self, user_id: str) -> bool:
        """
        Check if user has active session.

        Args:
            user_id: User identifier

        Returns:
            True if user has active session
        """
        return user_id in self.active_sessions

    def get_active_users(self) -> list[str]:
        """
        Get list of users with active sessions.

        Returns:
            List of user IDs
        """
        return list(self.active_sessions.keys())

    def get_session_count(self) -> int:
        """
        Get number of active sessions.

        Returns:
            Number of active sessions
        """
        return len(self.active_sessions)

    async def cancel_all_sessions(self):
        """
        Cancel all active sessions (e.g., during shutdown).
        """
        async with self._lock:
            for user_id, session in list(self.active_sessions.items()):
                session.cancel_token.cancel(reason="System shutdown")
                logger.info(f"Cancelled session for {user_id} due to shutdown")

            self.active_sessions.clear()

        logger.info("All sessions cancelled")
