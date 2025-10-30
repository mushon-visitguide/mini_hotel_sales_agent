"""Event emitter pattern for hooks and monitoring"""
import logging
from typing import Callable, Dict, List, Any
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


class EventEmitter:
    """
    Event emitter for hook-based architecture.

    Similar to Node.js EventEmitter or Gemini CLI's coreEvents.

    Usage:
        events = EventEmitter()

        # Register listener
        events.on('tool_complete', lambda tool, result: print(f"{tool} done"))

        # Emit event
        events.emit('tool_complete', tool_name='availability', result={...})
    """

    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = defaultdict(list)

    def on(self, event: str, callback: Callable):
        """
        Register a callback for an event.

        Args:
            event: Event name (e.g., 'before_tool', 'after_tool')
            callback: Function to call when event fires
        """
        self._listeners[event].append(callback)
        logger.debug(f"Registered listener for event: {event}")

    def off(self, event: str, callback: Callable):
        """Remove a specific callback from an event"""
        if event in self._listeners:
            self._listeners[event].remove(callback)

    def once(self, event: str, callback: Callable):
        """Register a callback that only fires once"""
        def wrapper(*args, **kwargs):
            callback(*args, **kwargs)
            self.off(event, wrapper)

        self.on(event, wrapper)

    async def emit(self, event: str, **data):
        """
        Emit an event to all registered listeners.

        Args:
            event: Event name
            **data: Data to pass to listeners
        """
        if event not in self._listeners:
            return

        for callback in self._listeners[event]:
            try:
                # Support both sync and async callbacks
                if callable(callback):
                    result = callback(**data)
                    # If it's a coroutine, await it
                    if hasattr(result, '__await__'):
                        await result
            except Exception as e:
                logger.error(f"Error in event listener for '{event}': {e}", exc_info=True)

    def emit_sync(self, event: str, **data):
        """
        Synchronous version of emit (for non-async contexts).

        Args:
            event: Event name
            **data: Data to pass to listeners
        """
        if event not in self._listeners:
            return

        for callback in self._listeners[event]:
            try:
                callback(**data)
            except Exception as e:
                logger.error(f"Error in event listener for '{event}': {e}", exc_info=True)

    def remove_all_listeners(self, event: str = None):
        """Remove all listeners for an event, or all events if event=None"""
        if event:
            self._listeners[event].clear()
        else:
            self._listeners.clear()

    def listener_count(self, event: str) -> int:
        """Get number of listeners for an event"""
        return len(self._listeners.get(event, []))


# Global event emitter instance for runtime events
runtime_events = EventEmitter()


class ToolMetrics:
    """Track tool execution metrics"""

    def __init__(self):
        self.tool_calls: Dict[str, int] = defaultdict(int)
        self.tool_durations: Dict[str, List[float]] = defaultdict(list)
        self.tool_errors: Dict[str, int] = defaultdict(int)
        self.total_executions = 0
        self.total_errors = 0

    def record_execution(self, tool_name: str, duration_ms: float, success: bool = True):
        """Record a tool execution"""
        self.tool_calls[tool_name] += 1
        self.tool_durations[tool_name].append(duration_ms)
        self.total_executions += 1

        if not success:
            self.tool_errors[tool_name] += 1
            self.total_errors += 1

    def get_stats(self, tool_name: str = None) -> Dict[str, Any]:
        """Get statistics for a tool or all tools"""
        if tool_name:
            durations = self.tool_durations.get(tool_name, [])
            return {
                "tool": tool_name,
                "total_calls": self.tool_calls.get(tool_name, 0),
                "total_errors": self.tool_errors.get(tool_name, 0),
                "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
                "min_duration_ms": min(durations) if durations else 0,
                "max_duration_ms": max(durations) if durations else 0,
            }
        else:
            # Overall stats
            all_durations = [d for durations in self.tool_durations.values() for d in durations]
            return {
                "total_executions": self.total_executions,
                "total_errors": self.total_errors,
                "success_rate": (self.total_executions - self.total_errors) / self.total_executions * 100 if self.total_executions > 0 else 0,
                "avg_duration_ms": sum(all_durations) / len(all_durations) if all_durations else 0,
                "tools": list(self.tool_calls.keys()),
            }

    def reset(self):
        """Reset all metrics"""
        self.tool_calls.clear()
        self.tool_durations.clear()
        self.tool_errors.clear()
        self.total_executions = 0
        self.total_errors = 0


# Global metrics tracker
tool_metrics = ToolMetrics()


def setup_default_logging_hooks():
    """
    Setup default logging hooks for runtime events.
    Call this at startup to enable automatic logging.
    """

    def log_tool_start(tool_id: str, tool_name: str, **kwargs):
        logger.info(f"🔧 [Tool Start] {tool_id}: {tool_name}")

    def log_tool_complete(tool_id: str, tool_name: str, duration_ms: float, **kwargs):
        logger.info(f"✓ [Tool Complete] {tool_id}: {tool_name} ({duration_ms:.0f}ms)")

    def log_tool_error(tool_id: str, tool_name: str, error: str, **kwargs):
        logger.error(f"✗ [Tool Error] {tool_id}: {tool_name} - {error}")

    def log_wave_start(wave_num: int, total_waves: int, tools: list, **kwargs):
        tool_names = [t.get('tool_name', t.get('tool')) for t in tools]
        logger.info(f"🌊 [Wave {wave_num}/{total_waves}] Starting {len(tools)} tools in parallel: {tool_names}")

    def log_wave_complete(wave_num: int, total_waves: int, duration_ms: float, **kwargs):
        logger.info(f"✓ [Wave {wave_num}/{total_waves}] Completed in {duration_ms:.0f}ms")

    def log_execution_cancelled(wave_num: int, total_waves: int, cancel_reason: str, partial_results_count: int, **kwargs):
        logger.warning(f"⚠ [Execution Cancelled] at wave {wave_num}/{total_waves} - {cancel_reason} ({partial_results_count} partial results)")

    def log_cancellation_handled(message: str, wave_num: int, partial_results_count: int, **kwargs):
        logger.info(f"✓ [Cancellation Handled] {message} - {partial_results_count} partial results preserved")

    runtime_events.on('tool_start', log_tool_start)
    runtime_events.on('tool_complete', log_tool_complete)
    runtime_events.on('tool_error', log_tool_error)
    runtime_events.on('wave_start', log_wave_start)
    runtime_events.on('wave_complete', log_wave_complete)
    runtime_events.on('execution_cancelled', log_execution_cancelled)
    runtime_events.on('cancellation_handled', log_cancellation_handled)

    logger.info("📊 Default logging hooks registered")


def setup_metrics_hooks():
    """
    Setup metrics tracking hooks.
    Call this at startup to enable automatic metrics collection.
    """

    def track_tool_execution(tool_name: str, duration_ms: float, **kwargs):
        tool_metrics.record_execution(tool_name, duration_ms, success=True)

    def track_tool_error(tool_name: str, duration_ms: float = 0, **kwargs):
        tool_metrics.record_execution(tool_name, duration_ms, success=False)

    runtime_events.on('tool_complete', track_tool_execution)
    runtime_events.on('tool_error', track_tool_error)

    logger.info("📈 Metrics tracking hooks registered")
