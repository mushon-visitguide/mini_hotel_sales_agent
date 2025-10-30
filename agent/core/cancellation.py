"""Cancellation token system for graceful operation cancellation"""
import asyncio
from threading import Lock


class CancellationToken:
    """
    Simple flag-based cancellation token for async operations.

    Thread-safe token that can be checked during execution to determine
    if the operation should be cancelled. Designed to work at wave boundaries
    in the runtime executor to ensure clean state.

    Usage:
        # Create token
        token = CancellationToken()

        # Start async operation
        task = asyncio.create_task(orchestrator.process_message(..., cancel_token=token))

        # Cancel from another context (e.g., when new message arrives)
        token.cancel()

        # Operation will stop gracefully after current wave completes
        try:
            result = await task
        except CancelledException:
            print("Operation was cancelled")
    """

    def __init__(self):
        """Initialize cancellation token with uncancelled state."""
        self._cancelled = False
        self._lock = Lock()
        self._cancel_reason = None

    def cancel(self, reason: str = None):
        """
        Cancel the operation.

        Thread-safe method to set cancellation flag. Can be called from
        any thread or async context.

        Args:
            reason: Optional reason for cancellation (e.g., "New message received")
        """
        with self._lock:
            self._cancelled = True
            self._cancel_reason = reason or "Operation cancelled"

    @property
    def is_cancelled(self) -> bool:
        """
        Check if operation has been cancelled.

        Thread-safe property that can be checked during execution.

        Returns:
            True if cancel() has been called, False otherwise
        """
        with self._lock:
            return self._cancelled

    @property
    def cancel_reason(self) -> str:
        """
        Get the reason for cancellation.

        Returns:
            Cancellation reason if set, None otherwise
        """
        with self._lock:
            return self._cancel_reason

    def reset(self):
        """
        Reset the token to uncancelled state.

        Useful for token reuse, though creating new tokens is recommended.
        """
        with self._lock:
            self._cancelled = False
            self._cancel_reason = None


class CancelledException(Exception):
    """
    Exception raised when an operation is cancelled via CancellationToken.

    This exception is raised at wave boundaries in the runtime executor
    when cancellation is detected. It should be caught and handled gracefully
    by the orchestrator to preserve partial results.

    Attributes:
        message: Description of cancellation
        partial_results: Any results completed before cancellation
        wave_num: Wave number where cancellation occurred
    """

    def __init__(self, message: str, partial_results: dict = None, wave_num: int = None):
        """
        Initialize cancellation exception.

        Args:
            message: Cancellation message
            partial_results: Results from waves that completed before cancellation
            wave_num: Wave number where cancellation was detected
        """
        super().__init__(message)
        self.message = message
        self.partial_results = partial_results or {}
        self.wave_num = wave_num

    def __str__(self):
        base = self.message
        if self.wave_num is not None:
            base += f" (at wave {self.wave_num})"
        if self.partial_results:
            base += f" - {len(self.partial_results)} partial results available"
        return base
